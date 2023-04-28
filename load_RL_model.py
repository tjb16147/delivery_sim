
import torch
import torch.nn as nn
import torch.optim as optim

from torch.distributions.normal import Normal
from torch.utils.tensorboard import SummaryWriter

import gymnasium as gym
import numpy as np

import os 
import time

from env import DeliveryEnv
import numpy as np

import signal

def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    torch.nn.init.orthogonal_(layer.weight, std)
    torch.nn.init.constant_(layer.bias, bias_const)
    return layer

def save_model(model, note):
    print("Saving model..")
    save_path = f"runs/trained_models/{run_name}_step_"+str(note)+".pth"
    torch.save(model, save_path)    

class Agent(nn.Module):
    def __init__(self, envs):
        super().__init__()

        obs_size = np.array(envs.single_observation_space.shape).prod()
        act_size = np.prod(envs.single_action_space.shape)

        self.critic = nn.Sequential(
                        layer_init(nn.Linear(obs_size, 64)),
                        nn.Tanh(),
                        layer_init(nn.Linear(64, 64)),
                        nn.Tanh(),
                        layer_init(nn.Linear(64, 1), std=1.0)
                        )

        self.actor_mean = nn.Sequential(
                        layer_init(nn.Linear(obs_size, 64)),
                        nn.Tanh(),
                        layer_init(nn.Linear(64, 64)),
                        nn.Tanh(),
                        layer_init(nn.Linear(64, act_size), std=0.01)
                        ) 
        self.actor_logstd = nn.Parameter(torch.zeros(1, act_size))
    

    def get_value(self, x):
        return self.critic(x)

    def get_action_and_value(self, x, action=None):
        action_mean = self.actor_mean(x)
        action_logstd = self.actor_logstd.expand_as(action_mean)
        action_std = torch.exp(action_logstd)

        probs = Normal(action_mean, action_std)

        if action is None:
            action = probs.sample()

        return action, probs.log_prob(action).sum(1), probs.entropy().sum(1), self.critic(x)



if __name__ == "__main__":


    run_name = time.time()
    writer = SummaryWriter(f"runs/{run_name}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


    num_envs = 24
    learning_rate = 0.01

    def make_env():
        def thunk():
            env = DeliveryEnv()
            env = gym.wrappers.NormalizeObservation(env)
            env = gym.wrappers.RecordEpisodeStatistics(env)
            return env
        return thunk

    envs = gym.vector.AsyncVectorEnv([make_env() for i in range(num_envs)])

    # Define the path to the saved model file
    # Don't forget to update the environment (i.e. object weight, friction) to match the model
    agent_path = "D:\\delivery_sim\\runs\\eval\\18-25cmsq_3kg_0.5f\\18-25cmsq_3kg_0.5f.pth"

    agent = Agent(envs).to(device)
    # load state dictionary
    agent.load_state_dict(torch.load(agent_path))
    # set evaluation mode
    agent.eval()
    optimizer = optim.Adam(agent.parameters(), lr=learning_rate, eps=1e-5)

    obs_shape = envs.single_observation_space.shape
    act_shape = envs.single_action_space.shape
    obs_size = np.array(obs_shape).prod()
    act_size = np.prod(act_shape)
    num_steps = 1012
    gamma = 0.99
    gae_lambda = 0.95
    batch_size = int(num_envs * num_steps)
    num_minibatches = 32
    minibatch_size = int(batch_size // num_minibatches)
    update_epochs  = 10 
    clip_coef  = 0.2
    ent_coef =  0.0
    vf_coef  =  0.5
    max_grad_norm = 0.5

    # storage setup
    obs = torch.zeros((num_steps, num_envs) + obs_shape).to(device)
    actions = torch.zeros((num_steps, num_envs) + act_shape).to(device)
    logprobs = torch.zeros((num_steps, num_envs)).to(device)
    rewards = torch.zeros((num_steps, num_envs)).to(device)
    dones   = torch.zeros((num_steps, num_envs)).to(device)
    values  = torch.zeros((num_steps, num_envs)).to(device)


    # start the game
    global_step = 0
    start_time = time.time()
    next_obs, _  = envs.reset()
    next_obs = torch.Tensor(next_obs).to(device)
    next_done = torch.zeros(num_envs).to(device)
    num_updates = 100000
    video_filenames = set()

    # save when triggered ctrl-c
    model = agent.state_dict()
    signal.signal(signal.SIGINT, lambda sig, frame: save_model(model, note))
    note = 0
    eval_cnt = 0

    for update in range(1, num_updates + 1):

        for step in range(0, num_steps): # small trajectory 
            global_step += 1*num_envs
            obs[step]   = next_obs
            dones[step] = next_done

            # Algo logic
            with torch.no_grad():
                action, logprob, _, value = agent.get_action_and_value(next_obs)
                values[step] = value.flatten()

            actions[step]  = action
            logprobs[step] = logprob

            next_obs, reward, terminated, truncated, infos = envs.step(action.cpu().numpy())
            done = np.logical_or(terminated, truncated)
            rewards[step] = torch.tensor(reward).to(device).view(-1)
            next_obs = torch.Tensor(next_obs).to(device)
            next_done = torch.Tensor(done).to(device)

            if "final_info" not in infos:
                continue


            for info in infos["final_info"]:
                if info is None:
                    continue
                print(f"global_step={global_step}, episodic_return={info['episode']['r']}")
                writer.add_scalar("charts/episodic_return", info["episode"]["r"], global_step)
                writer.add_scalar("charts/episodic_length", info["episode"]["l"], global_step)
                writer.add_scalar("charts/average_speed", 10.0 * actions.mean() ,global_step)
                if info["episode"]["r"] == 1:
                    eval_cnt += 1
                if eval_cnt == 5:
                    print('done')
                    quit()

                # log on each global_step
                #save_model(model, global_step)
            


        # bootstrap value if not done
        with torch.no_grad():
            next_value = agent.get_value(next_obs).reshape(1, -1)
            advantages = torch.zeros_like(rewards).to(device)
            lastgaelam = 0

            for t in reversed(range(num_steps)):
                if t == num_steps - 1:
                    nextnonterminal = 1.0 - next_done
                    nextvalues = next_value
                else:
                    nextnonterminal = 1.0 - dones[t+1]
                    nextvalues = values[t+1]

                delta = rewards[t] + gamma*nextvalues * nextnonterminal - values[t]
                advantages[t] = lastgaelam = delta + gamma * gae_lambda * nextnonterminal * lastgaelam

            returns = advantages + values


        # flatten the batch
        b_obs = obs.reshape( (-1,) + obs_shape )
        b_logprobs = logprobs.reshape(-1)
        b_actions  = actions.reshape( (-1,) + act_shape ) 
        b_advantages = advantages.reshape(-1)
        b_returns  = returns.reshape(-1)
        b_values   = values.reshape(-1)

        # optimizing the policy and value network

        b_inds = np.arange(batch_size)
        clipfracs = []

        for epoch in range(update_epochs):
            np.random.shuffle(b_inds)
            for start in range(0, batch_size, minibatch_size):
                end = start + minibatch_size
                mb_inds = b_inds[start:end]

                _, newlogprob, entropy, newvalue = agent.get_action_and_value(b_obs[mb_inds], b_actions[mb_inds])
                logratio = newlogprob - b_logprobs[mb_inds]
                ratio = logratio.exp()

                with torch.no_grad():
                    # calculate approx_kl 
                    old_approx_kl = (-logratio).mean()
                    approx_kl = ((ratio - 1) - logratio).mean()
                    clipfracs += [((ratio -1.0).abs() > clip_coef).float().mean().item()]


                mb_advantages = b_advantages[mb_inds]

                # norm advantage
                mb_advantages = (mb_advantages - mb_advantages.mean()) / (mb_advantages.std() + 1e-8)



                # policy loss

                pg_loss1 = -mb_advantages * ratio
                pg_loss2 = -mb_advantages * torch.clamp(ratio, 1-clip_coef, 1+clip_coef)
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()


                # value loss  

                newvalue = newvalue.view(-1)

                # clip vloss 
                v_loss_unclipped = (newvalue - b_returns[mb_inds]) ** 2
                v_clipped = b_values[mb_inds] + torch.clamp(
                                                newvalue - b_values[mb_inds],
                                                -clip_coef,
                                                clip_coef,
                                                )
                v_loss_clipped = (v_clipped - b_returns[mb_inds]) ** 2
                v_loss_max     = torch.max(v_loss_unclipped, v_loss_clipped)
                v_loss         = 0.5 * v_loss_max.mean()


                # entropy loss
                entropy_loss = entropy.mean()
                loss = pg_loss - ent_coef * entropy_loss + v_loss * vf_coef


                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), max_grad_norm)

                optimizer.step()

        # logging 
        y_pred, y_true = b_values.cpu().numpy(), b_returns.cpu().numpy()
        var_y = np.var(y_true)

        explained_var = np.nan if var_y == 0 else 1-np.var(y_true - y_pred)/var_y

        writer.add_scalar("charts/learning_rate", optimizer.param_groups[0]["lr"], global_step)
        writer.add_scalar("losses/value_loss", v_loss.item(), global_step)
        writer.add_scalar("losses/policy_loss", pg_loss.item(), global_step)
        writer.add_scalar("losses/entropy", entropy_loss.item(), global_step)
        writer.add_scalar("losses/old_approx_kl", old_approx_kl.item(), global_step)
        writer.add_scalar("losses/approx_kl", approx_kl.item(), global_step)
        writer.add_scalar("losses/clipfrac", np.mean(clipfracs), global_step)
        writer.add_scalar("losses/explained_variance", explained_var, global_step)
        print("SPS:", int(global_step / (time.time() - start_time)))
        writer.add_scalar("charts/SPS", int(global_step / (time.time() - start_time)), global_step)

    note = 'ctrl-c'
    save_model(model, note)

    envs.close()
    writer.close()