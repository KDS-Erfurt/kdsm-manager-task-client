from kdsm_manager_task_client import TaskClient


if __name__ == '__main__':
    with TaskClient(id=27, api_token="dHkdFgOB0LFLD6yeScYlvFrklixzKk6PjCDZmxiJb7Iv1Ga0RLYn7CgFRUb6U2sd") as task:
        raise Exception("Test")
        print()

    print()
