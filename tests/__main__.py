from tests import test1
from tests import test2

# for manual testing
# in project root directory, run:
# py -m tests
# py -m tests.test1
# py -m tests.test2

if __name__ == "__main__":
    # 下位レイヤー、上位レイヤーのテストケースを実行する
    # show the test menu and run the selected test cases
    print("[ choice test cases ]")

    print("1. test cases from tests/test1.py for cameraAPI()")
    print("2. test cases from tests/test2.py for camera()")

    choice = input("Enter the test case number (1 or 2) to run, or 'q' to quit: ")

    if choice == '1':
        # test1:test_cameraAPIs()を実行する
        test1.test_cameraAPIs()
    elif choice == '2':
        # test2:test_camera()を実行する
        test2.test_camera()
    elif choice.lower() == 'q':
        print("Exiting the test menu.")

    exit(0)
