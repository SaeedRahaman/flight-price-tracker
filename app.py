from jetblue import flight

def main():
    ddates = [
        "Mon Dec 19",
        "Tue Dec 20",
        "Wed Dec 21",
        "Thu Dec 23",
        "Fri Dec 24",
        "Sat Dec 25"
    ]

    rdates = [
        "Tue Jan 3",
        "Wed Jan 4",
        "Thu Jan 5",
        "Fri Jan 6",
    ]

    for d in ddates:
        for r in rdates:
            print(d, r)
            flight(d, r)

if __name__ == "__main__":
    main()

