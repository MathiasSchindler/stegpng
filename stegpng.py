#!/usr/bin/env python3
import sys
import json
import base64
from PIL import Image
import numpy as np
import subprocess
import os

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found. Please create it with 'cuda' and 'model_path' settings.")
    sys.exit(1)
except json.JSONDecodeError:
    print("Error: config.json is not valid JSON.")
    sys.exit(1)

def count_ones(value):
    """Counts the number of 1s in the first 7 bits."""
    return bin(value & 0b11111110).count('1')

def encode_bit(value, bit):
    """Encodes a bit into the value based on the parity of the first 7 bits."""
    ones = count_ones(value)
    current_lsb = value & 1
    
    if ones % 2 == 0:
        desired_lsb = 1 if bit else 0
    else:
        desired_lsb = 0 if bit else 1
        
    if current_lsb != desired_lsb:
        return value ^ 1
    return value

def decode_bit(value):
    """Decodes a bit from the value based on the parity of the first 7 bits."""
    ones = count_ones(value)
    lsb = value & 1
    
    if ones % 2 == 0:
        return 1 if lsb == 1 else 0
    else:
        return 0 if lsb == 1 else 1

def run_ts_sms_encode(message):
    """Calls ts_sms to encode the message."""
    try:
        cmd = ['./ts_sms']
        if config['cuda']:
            cmd.append('--cuda')
        cmd.extend(['-m', config['model_path'], '-F', 'base64', 'c', message])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running ts_sms (encode): {e}")
        sys.exit(1)

def run_ts_sms_decode(encoded_message):
    """Calls ts_sms to decode the message."""
    try:
        cmd = ['./ts_sms']
        if config['cuda']:
            cmd.append('--cuda')
        cmd.extend(['-m', config['model_path'], '-F', 'base64', 'd', encoded_message])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running ts_sms (decode): {e}")
        sys.exit(1)

def encode_message(image_path, message, output_path):
    """Encodes a message into an image."""
    # First encode the message with ts_sms
    encoded_message = run_ts_sms_encode(message)
    print(f"ts_sms encoded message: {encoded_message}")
    
    # Open the image and convert it to an array
    img = Image.open(image_path)
    pixels = np.array(img)
    
    # Convert the encoded message to bits
    message_bytes = encoded_message.encode('utf-8')
    message_bits = ''.join(format(byte, '08b') for byte in message_bytes)
    
    # Check if there's enough space
    max_bits = pixels.shape[0] * pixels.shape[1] * 3
    if len(message_bits) > max_bits:
        print(f"Error: Message too long. Maximum {max_bits//8} bytes possible.")
        sys.exit(1)
        
    # Store message length in first 32 bits
    length_bits = format(len(message_bits), '032b')
    bit_stream = length_bits + message_bits
    bit_index = 0
    
    # Iterate through all pixels
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            for k in range(3):  # RGB channels
                if bit_index < len(bit_stream):
                    pixels[i,j,k] = encode_bit(pixels[i,j,k], int(bit_stream[bit_index]))
                    bit_index += 1
                else:
                    break
                    
    # Save the new image
    Image.fromarray(pixels).save(output_path)
    print(f"Message successfully encoded in {output_path}.")

def decode_message(image_path):
    """Decodes a message from an image."""
    # Open the image and convert it to an array
    img = Image.open(image_path)
    pixels = np.array(img)
    
    # First read the message length from the first 32 bits
    length_bits = ''
    bit_count = 0
    
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            for k in range(3):  # RGB channels
                if bit_count < 32:
                    length_bits += str(decode_bit(pixels[i,j,k]))
                    bit_count += 1
                else:
                    break
                    
    message_length = int(length_bits, 2)
    
    # Read the actual message
    message_bits = ''
    bit_count = 0
    
    for i in range(pixels.shape[0]):
        for j in range(pixels.shape[1]):
            for k in range(3):  # RGB channels
                if bit_count >= 32 and (bit_count - 32) < message_length:
                    message_bits += str(decode_bit(pixels[i,j,k]))
                bit_count += 1
                
    # Convert bits back to bytes and then to text
    message_bytes = []
    for i in range(0, len(message_bits), 8):
        byte = message_bits[i:i+8]
        if len(byte) == 8:
            message_bytes.append(int(byte, 2))
            
    try:
        encoded_message = bytes(message_bytes).decode('utf-8')
        print(f"Base64 message extracted from image: {encoded_message}")
        decoded_message = run_ts_sms_decode(encoded_message)
        print(f"Decoded message: {decoded_message}")
    except UnicodeDecodeError:
        print("Error: No valid UTF-8 message found.")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("Encode: python stegpng.py encode <input_image> <message>")
        print("Decode: python stegpng.py decode <input_image>")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "encode":
        if len(sys.argv) != 4:
            print("Error: Please specify input image and message.")
            sys.exit(1)
        input_image = sys.argv[2]
        message = sys.argv[3]
        output_image = input_image.rsplit('.', 1)[0] + '-enc.png'
        encode_message(input_image, message, output_image)
        
    elif command == "decode":
        if len(sys.argv) != 3:
            print("Error: Please specify input image.")
            sys.exit(1)
        input_image = sys.argv[2]
        decode_message(input_image)
        
    else:
        print("Error: Unknown command. Use 'encode' or 'decode'.")
        sys.exit(1)

if __name__ == "__main__":
    main()