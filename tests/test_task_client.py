import random
import time

from kdsm_manager_task_client import Task, Subtask

task = Task()


class Sub1(Subtask):
    def payload(self):
        with self.step("Step 1"):
            self.logger.info("sub1.step1 payload")
            time.sleep(random.randint(1, 10))

        with self.step("Step 2"):
            self.logger.info("sub1.step2 payload")
            time.sleep(random.randint(1, 10))

        with self.step("Step 3"):
            self.logger.info("sub1.step3 payload")
            time.sleep(random.randint(1, 10))


class Sub2(Subtask):
    def payload(self):
        with self.step("Step 1"):
            self.logger.info("sub2.step1 payload")
            time.sleep(random.randint(1, 10))

        with self.step("Step 2"):
            self.logger.info("sub2.step2 payload")
            time.sleep(random.randint(1, 10))

        with self.step("Step 3"):
            self.logger.info("sub2.step3 payload")
            time.sleep(random.randint(1, 10))


class Sub3(Subtask):
    def payload(self):
        with self.step("Step 1"):
            self.logger.info("sub3.step1 payload")
            time.sleep(random.randint(1, 10))

        with self.step("Step 2"):
            self.logger.info("sub3.step2 payload")
            time.sleep(random.randint(1, 10))

        with self.step("Step 3"):
            self.logger.info("sub3.step3 payload")
            time.sleep(random.randint(1, 10))


task.subtask(Sub1(steps=3), Sub2(steps=3), Sub3(steps=3), delete_subtasks=True)

if __name__ == '__main__':
    task.run()
