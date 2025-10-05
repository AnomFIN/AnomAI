import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python make_ico.py <input.png> <output.ico>")
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    try:
        from PIL import Image
    except Exception:
        print("Pillow not installed. Run: pip install pillow")
        sys.exit(2)
    img = Image.open(inp).convert("RGBA")
    sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
    img.save(outp, format='ICO', sizes=sizes)
    print(f"Wrote {outp}")

if __name__ == '__main__':
    main()

