#!/usr/bin/env python3
import argparse
import wave
import random

def bits_to_text(bits: str) -> str:
    chars = []
    for i in range(0, len(bits), 8):
        chunk = bits[i:i+8]
        if len(chunk) < 8:
            break
        chars.append(chr(int(chunk, 2)))
    return ''.join(chars)

def read_wav_samples(path: str):
    with wave.open(path, "rb") as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())

    if params.nchannels != 1 or params.sampwidth != 2:
        raise ValueError("Only mono 16-bit PCM WAV is supported")

    data = bytearray(frames)
    samples = []
    for i in range(0, len(data), 2):
        value = int.from_bytes(bytes([data[i], data[i+1]]), byteorder="little", signed=True)
        samples.append(value)
    return params, samples

def recover(cover_wav, stego_wav, output_txt, log_file, key, frame_size, delta, msg_len):
    _, cover_samples = read_wav_samples(cover_wav)
    _, stego_samples = read_wav_samples(stego_wav)

    total_samples = min(len(cover_samples), len(stego_samples))
    total_frames = total_samples // frame_size
    total_bits = msg_len * 8

    if total_bits > total_frames:
        raise ValueError("Audio too short for requested message length")

    random.seed(key)
    bits = []
    lines = []

    for frame_idx in range(total_bits):
        frame_start_sample = frame_idx * frame_size
        hop_offset = random.randint(0, frame_size - 1)
        target_sample = frame_start_sample + hop_offset

        cover_value = cover_samples[target_sample]
        stego_value = stego_samples[target_sample]
        diff = stego_value - cover_value

        bit = '1' if diff > 0 else '0'
        bits.append(bit)

        lines.append(
            f"frame={frame_idx} hop_offset={hop_offset} sample={target_sample} "
            f"cover={cover_value} stego={stego_value} diff={diff} recovered_bit={bit}"
        )

    text = bits_to_text(''.join(bits))

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(text)

    with open(log_file, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print("RUN_OK")
    print(f"OUTPUT_FILE={output_txt}")
    print(f"LOG_FILE={log_file}")
    print(f"RECOVERED_TEXT={text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cover", default="cover.wav")
    parser.add_argument("--input", default="stego.wav")
    parser.add_argument("--output", default="extracted.txt")
    parser.add_argument("--log", default="recover.log")
    parser.add_argument("--key", type=int, required=True)
    parser.add_argument("--frame-size", type=int, required=True)
    parser.add_argument("--delta", type=int, required=True)
    parser.add_argument("--msg-len", type=int, default=9)
    args = parser.parse_args()

    recover(args.cover, args.input, args.output, args.log, args.key, args.frame_size, args.delta, args.msg_len)
