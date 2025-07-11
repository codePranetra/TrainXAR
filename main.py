# main.py

from chat_logic import get_answer

def main():
    user_id = input("Enter user ID: ")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break

        answer = get_answer(user_input, user_id)
        print(answer)

if __name__ == "__main__":
    main()
