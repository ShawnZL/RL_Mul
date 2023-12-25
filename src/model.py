import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import datetime
import time
from src.scl_session import SCLSession as SCLGame
from src.fpga_session import FPGASession as FPGAGame


def log(message):
    print('[DRiLLS {:%Y-%m-%d %H:%M:%S}] {}'.format(datetime.datetime.now(), message))


class Normalizer:
    def __init__(self, num_inputs):
        self.num_inputs = num_inputs
        self.n = torch.zeros(num_inputs)
        self.mean = torch.zeros(num_inputs)
        self.mean_diff = torch.zeros(num_inputs)
        self.var = torch.zeros(num_inputs)

    def observe(self, x):
        if x is not None:
            self.n += 1.
            last_mean = torch.clone(self.mean)
            x = torch.from_numpy(x)
            self.mean += (x - self.mean) / self.n
            self.mean_diff += (x - last_mean) * (x - self.mean)
            self.var = torch.clip(self.mean_diff / self.n, min=1e-2, max=1000000000)

    def normalize(self, inputs):
        inputs = torch.from_numpy(inputs)
        obs_std = torch.sqrt(self.var)
        return (inputs - self.mean) / obs_std

    def reset(self):
        self.n = torch.zeros(self.num_inputs)
        self.mean = torch.zeros(self.num_inputs)
        self.mean_diff = torch.zeros(self.num_inputs)
        self.var = torch.zeros(self.num_inputs)


class A2C(nn.Module):
    def __init__(self, options, load_model=False, fpga_mapping=False):
        super(A2C, self).__init__()

        if fpga_mapping:
            self.game = FPGAGame(options)
        else:
            self.game = SCLGame(options)

        self.num_actions = self.game.action_space_length
        self.state_size = self.game.observation_space_size
        self.normalizer = Normalizer(self.state_size)
        self.epsilon = 0.2
        self.critic = self.Critic(9)
        self.actor = self.Actor(9, 7)
        self.actor_optimizer = optim.Adam(self.parameters(), lr=0.01)
        self.critic_optimizer = optim.Adam(self.parameters(), lr=0.01)

        # model saving/restoring
        self.model_dir = options['model_dir']

        if load_model:
            self.load_state_dict(torch.load(self.model_dir))
            log("Model restored.")
        else:
            torch.save(self.state_dict(), self.model_dir)

        self.gamma = 0.99

    class Critic(nn.Module):
        def __init__(self, state_size):
            super(A2C.Critic, self).__init__()
            self.fc1 = nn.Linear(state_size, 10)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(10, 1)

        def forward(self, x):
            x = self.fc1(x)
            x = self.relu(x)
            x = self.fc2(x)
            return x

    class Actor(nn.Module):
        def __init__(self, state_size, num_actions):
            super(A2C.Actor, self).__init__()
            self.fc1 = nn.Linear(state_size, 20)
            self.relu1 = nn.ReLU()
            self.fc2 = nn.Linear(20, 20)
            self.relu2 = nn.ReLU()
            self.fc3 = nn.Linear(20, num_actions)

        def forward(self, x):
            x = self.fc1(x)
            x = self.relu1(x)
            x = self.fc2(x)
            x = self.relu2(x)
            x = self.fc3(x)
            return x

    def forward(self, state):
        value = self.critic(state)
        action_probs = F.softmax(self.actor(state), dim=-1)
        return action_probs, value

    # def loss(self, action_probs, value, actions, discounted_rewards):
    #     # critic loss
    #     advantage = discounted_rewards - value
    #     critic_loss = torch.sum(torch.square(advantage))
    #
    #     # actor loss
    #     neg_log_prob = F.cross_entropy(action_probs, actions, reduction='none')
    #     actor_loss = torch.sum(neg_log_prob * advantage)
    #
    #     return critic_loss + actor_loss

    def save_model(self):
        torch.save(self.state_dict(), self.model_dir)
        log("Model saved in path: {}".format(self.model_dir))

    def train_episode(self):
        state = self.game.reset()
        self.normalizer.reset()
        self.normalizer.observe(state)
        state = self.normalizer.normalize(state)
        print(f'state is {state}')
        done = False

        episode_states = []
        episode_actions = []
        episode_rewards = []

        # while not done:
        while not done:
            log('  iteration: ' + str(self.game.iteration))
            if state is not None:  # Check if state is not None
                state = torch.tensor(state, dtype=torch.float32).unsqueeze(0).detach()  # Add batch dimension
                action_probs, _ = self.forward(state)
                if action_probs is None:
                    print(f'{self.game.iteration} action_probs is None')
                    continue
                print(f'action_probs is {action_probs}')
                action_probs = action_probs.detach().numpy()
                # action 选择任务，greed选择
                if np.random.random() < self.epsilon:
                    action = np.random.choice(range(self.num_actions))
                    print(f'action greedy is {action}')
                else:
                    # action = np.random.choice(range(self.num_actions), p=action_probs.ravel())
                    action = np.argmax(action_probs)
                    print(f'action max is {action}')
                print(f'action is {action}')
                new_state, reward, done, _ = self.game.step(action)
                if new_state is None:
                    print(f'{self.game.iteration} new_state is None')
                    continue
                print(f'new_state is {new_state}')
                # append this step
                episode_states.append(state.numpy())
                action_ = np.zeros(self.num_actions)
                action_[action] = 1
                episode_actions.append(action_)
                episode_rewards.append(reward)

                # 时序差分目标
                new_state = torch.tensor(new_state, dtype=torch.float32)
                td_target = reward + self.gamma * self.critic(new_state) * (1 - done)
                td_delta = td_target - self.critic(state)  # 时序差分误差
                action = torch.tensor(action, dtype=torch.long)
                print(self.actor(new_state).shape)
                log_probs = torch.log(self.actor(new_state).gather(0, action))
                actor_loss = torch.mean(-log_probs * td_delta.detach())
                # 均方误差损失函数
                critic_loss = torch.mean(
                    F.mse_loss(self.critic(state), td_target.unsqueeze(1).detach()))
                self.actor_optimizer.zero_grad()
                self.critic_optimizer.zero_grad()
                actor_loss.backward()  # 计算策略网络的梯度
                critic_loss.backward()  # 计算价值网络的梯度
                self.actor_optimizer.step()  # 更新策略网络的参数
                self.critic_optimizer.step()  # 更新价值网络的参数

                state = new_state
                state = state.numpy()
                self.normalizer.observe(state)
                state = self.normalizer.normalize(state)

            else:
                log("Warning: state is None. Skipping iteration.")

        # Now that we have run the episode, we use this data to train the agent
        start = time.time()
        end = time.time()
        log('Episode Agent Training Time ~ ' + str((end - start) / 60) + ' minutes.')

        self.save_model()

        return np.sum(episode_rewards)

    def discount_and_normalize_rewards(self, episode_rewards):
        discounted_episode_rewards = np.zeros_like(episode_rewards)
        cumulative = 0.0
        for i in reversed(range(len(episode_rewards))):
            cumulative = cumulative * self.gamma + episode_rewards[i]
            discounted_episode_rewards[i] = cumulative

        mean = np.mean(discounted_episode_rewards)
        std = np.std(discounted_episode_rewards)
        if std == 0:
            std = 1e-8
        discounted_episode_rewards = (discounted_episode_rewards - mean) / std

        return discounted_episode_rewards