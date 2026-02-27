def compare(file1, file2):
    with open(file1, "r") as f1:
        with open(file2, "r") as f2:
            return f1.read() == f2.read()


def main():
    file1_path = "../sender/gbn.txt"
    file2_path = "recv.txt"

    if compare(file1_path, file2_path):
        print("Congrats! Files are the same! :>")
    else:
        print("Ops! Files are different. :<")


if __name__ == "__main__":
    main()
