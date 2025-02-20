import random
import time

from kdsm_manager_task_client import Task, Group, Subtask

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


task.subtask(Group(Sub1(name="A_sub1", steps=3),
                   Sub2(name="A_sub2", steps=3),
                   Sub3(name="A_sub3", steps=3)),
             Group(Sub1(name="B_sub1", steps=3),
                   Sub2(name="B_sub2", steps=3),
                   Sub3(name="B_sub3", steps=3)), delete_subtasks=True)

if __name__ == '__main__':
    task.run()
