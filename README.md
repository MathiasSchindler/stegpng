# StegPNG

StegPNG is a steganography tool that hides compressed text messages in PNG images. It uses the least significant bits (LSB) of the RGB color channels to embed the message.

## Example

Original image (wikismall2.png):

![Original Wikipedia Logo](wikismall2.png)

Image with hidden message (wikismall2-enc.png):

![Wikipedia Logo with hidden message](wikismall2-enc.png)

Can you spot the difference? The second image contains the complete Wikipedia article introduction about steganography (over 2200 characters) hidden in its pixels. The changes are so subtle they are virtually invisible to the human eye.

You can verify this yourself by running:
```bash
python stegpng.py decode wikismall2-enc.png
```

## Important Disclaimers

- This is a proof of concept and should not be used for serious applications
- The implementation does not fulfill the requirements for proper steganography - it does not ensure that the presence of a hidden message is undetectable
- The method is not robust against format changes, conversions, or image cropping
- Parts of the source code were created with assistance from Claude.ai

## Features & Limitations

- Text messages are compressed using ts_sms before embedding
- Maximum input text length is approximately 3800 bytes
- Compressed messages are typically around 2500 bits or less (significantly smaller for shorter messages)
- A 30x30 pixel PNG is usually sufficient for storage
- The same model is required for successful decompression
- Currently only the rwkv_169M_q8.bin model produces consistent results between CPU and GPU usage

## Requirements

- Python 3.8+
- ts_sms binary and model (available for Windows and Linux at https://bellard.org/ts_sms/)
- CUDA-capable GPU (optional)
- Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/stegpng.git
cd stegpng
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Download and install ts_sms from https://bellard.org/ts_sms/

4. Create a config.json file:
```json
{
    "cuda": true,
    "model_path": "path/to/your/model.bin"
}
```
Set `cuda` to `false` if you don't have a CUDA-capable GPU.

## Usage

### Encoding a message:
```bash
python stegpng.py encode input.png "Your secret message"
```
This will create `input-enc.png` containing your hidden message.

### Decoding a message:
```bash
python stegpng.py decode input-enc.png
```
This will display the hidden message.

## Technical Details

The tool works by:
1. Compressing the input text using ts_sms
2. Converting the compressed data to binary
3. Storing the message length in the first 32 bits
4. Using parity-based LSB encoding in the RGB channels
5. Saving the modified image

## Models and Compression

The compression rate varies significantly depending on the model used:

![Compression Performance vs Model Size](compression_tradeoff.png)

- **rwkv_169M_q8** is the default model, chosen for its consistent results between CPU and GPU usage
- **llama32-1B-q4** (Llama 3.2-1B with 4-bit quantization) offers significantly better compression but requires more storage
- **llama32-3B-q8** (Llama 3.2-3B with 8-bit quantization) provides even better compression at the cost of a larger model size

As shown in the graph, there is a trade-off between model size and compression performance (lower bits per byte is better). While larger models generally achieve better compression, they also require more storage space and computational resources.

## Credits

- ts_sms is developed by Fabrice Bellard and available at https://bellard.org/ts_sms/
- Parts of the source code were created with assistance from Claude.ai

## License

This project is released under CC0 (Creative Commons Zero).
