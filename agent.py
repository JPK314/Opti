from rocket_learn.agent.actor_critic_agent import ActorCriticAgent
from rocket_learn.agent.discrete_policy import DiscretePolicy
from torch.nn import Linear
from torch import nn
import torch as th
from typing import Tuple
import numpy as np
import torch.nn.functional as F
from torch.distributions import Categorical
from torch.nn.init import xavier_uniform


class ActorCriticEmbedderAgent(ActorCriticAgent):
    def __init__(self, actor, critic, embedder: Linear, optimizer):
        return NotImplemented
        super().__init__(actor=actor, critic=critic, optimizer=optimizer)
        self.embedder = embedder

    def forward(self, *args, **kwargs):
        embedded = self.embedder(args[-1])
        obs = args[:-1]
        obs.extend(th.max(embedded, -2))
        return self.actor(obs, **kwargs), self.critic(obs, **kwargs)


class DiscreteEmbed(DiscretePolicy):
    def __init__(self, net: nn.Module,  embedder: Linear, shape: Tuple[int, ...] = (3,) * 5 + (2,) * 3, deterministic=False):
        return NotImplemented
        super ().__init__(net=net, shape=shape, deterministic=deterministic)
        self.embedder = embedder

    def forward(self, obs):
        embedded = self.embedder(obs[1])
        new_obs = obs[0]
        new_obs.extend(th.max(embedded, -2))
        logits = self.net(new_obs)
        return logits

    def get_action_distribution(self, obs):
        if isinstance(obs, np.ndarray):
            obs = th.from_numpy(obs).float()
        elif isinstance(obs, tuple):
            obs = tuple(o if isinstance(o, th.Tensor) else th.from_numpy(o).float() for o in obs)


        logits = self(obs)

        if isinstance(logits, th.Tensor):
            logits = (logits,)

        max_shape = max(self.shape)
        logits = th.stack(
            [
                l
                if l.shape[-1] == max_shape
                else F.pad(l, pad=(0, max_shape - l.shape[-1]), value=float("-inf"))
                for l in logits
            ],
            dim=1
        )

        return Categorical(logits=logits)


class Opti(nn.Module):  # takes an embedder and a network and runs the embedder on the car obs before passing to the network
    def __init__(self, embedder: nn.Module, net: nn.Module):
        super().__init__()
        self.embedder = embedder
        self.net = net
        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                xavier_uniform(p)

    def forward(self, inp: tuple):
        main, cars = inp
        shaped_cars = th.reshape(cars, (len(main), 5, len(cars[0])))
        out = th.max(self.embedder(shaped_cars), -2)[0]
        result = self.net(th.cat((main, out), dim=1))
        return result
