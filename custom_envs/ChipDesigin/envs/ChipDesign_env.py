"""
Microgrid-simulation to OpenAI gym
V 0.1
"""
import gym
import os
import re
import datetime
import numpy as np
from subprocess import check_output
from src.features import extract_features

class LogicSynthesisEnv(gym.Env):
    def __init__(self, params):
        super(LogicSynthesisEnv, self).__init__()
        self.params = params

        self.episode_dir = None
        # Define action and observation space
        self.action_space = gym.spaces.Discrete(7)
        # number of features
        self.observation_space = 9

        self.iteration = 0
        self.episode = 0
        # self.sequence = ['strash']
        # LUT6 level
        self.lut_6, self.levels = float('inf'), float('inf')
        # 时延，面积大小
        self.delay, self.area = float('inf'), float('inf')
        # (value value index index)
        self.best_known_area = (float('inf'), float('inf'), -1, -1)
        self.best_known_delay = (float('inf'), float('inf'), -1, -1)
        self.best_known_area_meets_constraint = (float('inf'), float('inf'), -1, -1)

        self.best_known_lut_6 = (float('inf'), float('inf'), -1, -1)
        self.best_known_levels = (float('inf'), float('inf'), -1, -1)
        self.best_known_lut_6_meets_constraint = (float('inf'), float('inf'), -1, -1)



        # logging
        self.log = None

    def reset(self):
        """
        resets the environment and returns the state
        """
        self.iteration = 0
        self.episode += 1
        self.lut_6, self.levels = float('inf'), float('inf')
        self.delay, self.area = float('inf'), float('inf')
        self.episode_dir = os.path.join(self.params['playground_dir'], str(self.episode))
        if not os.path.exists(self.episode_dir):
            os.makedirs(self.episode_dir)

        # logging
        log_file = os.path.join(self.episode_dir, 'log.csv')
        if self.log:
            self.log.close()
        self.log = open(log_file, 'w')
        self.log.write('iteration, optimization, LUT-6, Levels, best LUT-6 meets constraint, best LUT-6, best levels\n')

        state, _ = self._run()
        return state

    def step(self, action):
        """
        accepts optimization index and returns (new state, reward, done, info)
        """
        self.sequence.append(self.params['optimizations'][action])
        new_state, reward = self._run_synthesis()

        # logging
        if self.lut_6 < self.best_known_lut_6[0]:
            self.best_known_lut_6 = (int(self.lut_6), int(self.levels), self.episode, self.iteration)
        if self.levels < self.best_known_levels[1]:
            self.best_known_levels = (int(self.lut_6), int(self.levels), self.episode, self.iteration)
        if self.levels <= self.params['fpga_mapping']['levels'] and self.lut_6 < self.best_known_lut_6_meets_constraint[
            0]:
            self.best_known_lut_6_meets_constraint = (int(self.lut_6), int(self.levels), self.episode, self.iteration)
        self.log.write(
            ', '.join([str(self.iteration), self.sequence[-1], str(int(self.lut_6)), str(int(self.levels))]) + ', ' +
            '; '.join(list(map(str, self.best_known_lut_6_meets_constraint))) + ', ' +
            '; '.join(list(map(str, self.best_known_lut_6))) + ', ' +
            '; '.join(list(map(str, self.best_known_levels))) + '\n')
        self.log.flush()

        done = self._is_episode_done()
        info = {}  # Additional information if needed
        return new_state, reward, done, info

    def render(self):
        # Visualize the current state if needed
        pass

    def _create_episode_directory(self):
        episode_dir = os.path.join(self.params['playground_dir'], str(self.episode))
        os.makedirs(episode_dir, exist_ok=True)
        return episode_dir

    def _apply_action(self, action):
        self.sequence.append(self.params['optimizations'][action])

    def _run(self):
        """
        run yosys on the given design file with the sequence of commands
        """
        self.iteration += 1
        output_design_file = os.path.join(self.episode_dir, f"{self.iteration}.v")
        output_design_file_mapped = os.path.join(self.episode_dir, f"{self.iteration}-mapped.v")

        # yosys 命令

        try:
            proc = check_output(["yosys", yosys_script])
            lut_6, levels = self._get_metrics(proc)
            reward = self._get_reward(lut_6, levels)
            self.lut_6, self.levels = lut_6, levels
            state = self._get_state(output_design_file)
            return state, reward
        except Exception as e:
            print(f"Error: {e}")
            return None, None

    def _is_episode_done(self):
        # Add logic to determine if the episode is done based on your criteria
        return self.iteration == self.params['iterations']

    def _get_metrics(self, stats):
        """
        parse LUT count and levels from the stats command of ABC
        """
        line = stats.decode("utf-8").split('\n')[-2].split(':')[-1].strip()

        ob = re.search(r'lev *= *[0-9]+', line)
        levels = int(ob.group().split('=')[1].strip())

        ob = re.search(r'nd *= *[0-9]+', line)
        lut_6 = int(ob.group().split('=')[1].strip())

        return lut_6, levels

    def _get_reward(self, lut_6, levels):
        constraint_met = True
        optimization_improvement = 0  # (-1, 0, 1) <=> (worse, same, improvement)
        constraint_improvement = 0  # (-1, 0, 1) <=> (worse, same, improvement)

        # check optimizing parameter
        if lut_6 < self.lut_6:
            optimization_improvement = 1
        elif lut_6 == self.lut_6:
            optimization_improvement = 0
        else:
            optimization_improvement = -1

        # check constraint parameter
        if levels > self.params["fpga_mapping"]["levels"]:
            constraint_met = False
            if levels < self.levels:
                constraint_improvement = 1
            elif levels == self.levels:
                constraint_improvement = 0
            else:
                constraint_improvement = -1

        # now calculate the reward
        return self._reward_table(constraint_met, constraint_improvement, optimization_improvement)

    def _reward_table(self, constraint_met, contraint_improvement, optimization_improvement):
        return {
            True: {
                0: {
                    1: 3,
                    0: 0,
                    -1: -1
                }
            },
            False: {
                1: {
                    1: 3,
                    0: 2,
                    -1: 1
                },
                0: {
                    1: 2,
                    0: 0,
                    -1: -2
                },
                -1: {
                    1: -1,
                    0: -2,
                    -1: -3
                }
            }
        }[constraint_met][contraint_improvement][optimization_improvement]

    def _get_state(self, design_file):
        return extract_features(design_file, self.params['yosys_binary'], self.params['abc_binary'])