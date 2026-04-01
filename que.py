# Queue of customers
queue = []

while True:
    print("\n===== CUSTOMER SERVICE QUEUE =====")
    print("1. Add Customer")
    print("2. Show Next Customer to Serve")
    print("3. Display Length of Queue")
    print("4. Check People Ahead of a Customer")
    print("5. Exit")

    choice = int(input("Enter your choice: "))

    if choice == 1:
        name = input("Enter customer name: ")
        queue.append(name)
        print(name, "added to the queue.")

    elif choice == 2:
        if len(queue) == 0:
            print("No customers in queue.")
        else:
            print("Next customer to serve:", queue[0])

    elif choice == 3:
        print("Number of customers waiting:", len(queue))

    elif choice == 4:
        name = input("Enter customer name: ")
        if name in queue:
            position = queue.index(name)
            print("People ahead of", name, ":", position)
        else:
            print("Customer not found in queue.")

    elif choice == 5:
        print("Exiting program...")
        break

    else:
        print("Invalid choice. Try again.")