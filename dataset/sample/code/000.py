def book_flight(): 
    request_initiated = True
    
    while request_initiated:
        # Prompt for flight ID 
        flight_id = request_flight_id()
    
        # Check availability
        if check_availability(flight_id):
            # Inform availability and request user info inform_user_available()
            user_id = request_user_id()
            user_name = request_user_name()
            
            # Attempt reservation
            reservation_result = reserve_flight(flight_id, user_id , user_name)
            if reservation_result['is_successful']:
                # Inform success and provide details
                inform_reservation_success(reservation_result)
                
                # Ask if user wants another booking
                if user_wants_to_book_another(): 
                    continue
                else:
                    request_initiated = False 
                    inform_user_contact_again()
            else:
                # Inform failure and ask if user wants to try again
                inform_reservation_failure()
                if user_wants_to_try_again():
                    continue 
                else:
                    request_initiated = False 
                    inform_user_contact_again()
        else:
            # Inform unavailability and ask if user wants to book another flight
            inform_user_unavailable()
            if user_wants_to_book_another():
                continue 
            else:
                request_initiated = False 
                inform_user_contact_again()

def request_flight_id():
    return input("Please provide the flight ID: ")

def check_availability(flight_id):
    # Simulate check availability (always returns True for this example)
    return True

def inform_user_available(): 
    print("The flight is available.")

def request_user_id():
    return input("Please provide your ID number: ")

def request_user_name():
    return input("Please provide your full name: ")

def reserve_flight(flight_id , user_id , user_name):
    # Simulate reservation (always succeeds for this example )
    return {'is_successful': True, 'flight_details': 'Flight  AA123 at 7:00 AM on April 5'}

def inform_reservation_success(reservation_result): 
    print("Reservation succeeded.") 
    print(f"Booking details: {reservation_result}")

def user_wants_to_book_another():
    response = input("Do you want to book another flight? ( yes/no): ").strip().lower()
    return response == "yes"

def inform_user_contact_again(): 
    print("Thank you! Please contact us again for future  needs.")

def inform_reservation_failure(): 
    print("Reservation failed.")

def user_wants_to_try_again():
    response = input("Do you want to try again? (yes/no): ") .strip().lower()
    return response == "yes"

def inform_user_unavailable(): 
    print("The flight is unavailable.")

# Start booking process
book_flight()
