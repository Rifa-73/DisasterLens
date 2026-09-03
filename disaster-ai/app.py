import json
from ai_model import analyze_image, transcribe_audio


def main():
    choice = input("Enter 1 for image, 2 for audio: ")

    try:
        if choice == "1":
            path = input("Enter image path: ")
            description = input("Enter description: ")
            result = analyze_image(path, description)

        elif choice == "2":
            path = input("Enter audio path: ")
            text = transcribe_audio(path)

            print("\n========== TRANSCRIPTION ==========")
            print(text)
            print("===================================")
            return

        else:
            print("Invalid choice.")
            return

        print("\n========== AI ASSESSMENT ==========")
        print(json.dumps(result, indent=2))
        print("===================================")

    except Exception as e:
        print("\nAI analysis failed:")
        print(e)


if __name__ == "__main__":
    main()