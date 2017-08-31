"""
Script used to train test platooning on a single lane.

RL vehicles are bunched together. The emergent behavior we are hoping to witness
is that rl-vehicles group together in other to allow non rl-vehicles a larger headway,
and thus larger equilibrium speeds.

One concern is whether rl-vehicles will start trail-gating human vehicles.
"""

import logging

from rllab.envs.normalized_env import normalize
from rllab.misc.instrument import stub, run_experiment_lite
from rllab.algos.trpo import TRPO
from rllab.baselines.linear_feature_baseline import LinearFeatureBaseline
from rllab.policies.gaussian_mlp_policy import GaussianMLPPolicy
from rllab.envs.gym_env import GymEnv


# from cistar.core.exp import SumoExperiment
from cistar.envs.loop_accel import SimpleAccelerationEnvironment
from cistar.scenarios.loop.loop_scenario import LoopScenario
from cistar.controllers.rlcontroller import RLController
from cistar.controllers.lane_change_controllers import *
from cistar.controllers.car_following_models import *


num_cars = 22
num_auto = 3


def run_task(*_):
    import cistar.envs as cistar_envs
    logging.basicConfig(level=logging.INFO)

    sumo_params = {"time_step": 0.1, "starting_position_shuffle": False, "vehicle_arrangement_shuffle": False,
                   "rl_lc": "aggressive", "human_lc": "aggressive", "rl_sm": "aggressive", "human_sm": "no_collide"}
    sumo_binary = "sumo"

    env_params = {"target_velocity": 8, "max-deacc": -6, "max-acc": 3,
                  "observation_vel_std": 0, "observation_pos_std": 0, "human_acc_std": 0, "rl_acc_std": 0,
                  "num_steps": 1500}

    net_params = {"length": 230, "lanes": 1, "speed_limit": 30, "resolution": 40,
                  "net_path": "debug/net/"}

    cfg_params = {"start_time": 0, "end_time": 30000, "cfg_path": "debug/rl/cfg/"}

    initial_config = {"shuffle": False}

    type_params = [("rl", num_auto, (RLController, {}), None, 0),
                   ("idm", num_cars - num_auto, (IDMController, {}), (StaticLaneChanger, {}), 0)]

    scenario = LoopScenario(exp_tag, type_params, net_params, cfg_params, initial_config=initial_config)

    from cistar import pass_params
    env_name = "SimpleAccelerationEnvironment"
    pass_params = (env_name, sumo_params, sumo_binary, type_params, env_params, net_params,
                cfg_params, initial_config, scenario)

    env = GymEnv(env_name, record_video=False, register_params=pass_params)
    horizon = env.horizon
    env = normalize(env)

    policy = GaussianMLPPolicy(
        env_spec=env.spec,
        hidden_sizes=(100, 50, 25)
    )

    baseline = LinearFeatureBaseline(env_spec=env.spec)

    algo = TRPO(
        env=env,
        policy=policy,
        baseline=baseline,
        batch_size=15000,
        max_path_length=horizon,
        n_itr=1000,
        # whole_paths=True,
        discount=0.999,
        step_size=0.01,
    )
    algo.train(),

exp_tag = str(num_cars) + '-car-' + str(num_auto) + '-rl-single-lane-platooning-no-failsafe'

for seed in [5]:  # [16, 20, 21, 22]:
    run_experiment_lite(
        run_task,
        # Number of parallel workers for sampling
        n_parallel=8,
        # Only keep the snapshot parameters for the last iteration
        snapshot_mode="all",
        # Specifies the seed for the experiment. If this is not provided, a random seed
        # will be used
        seed=seed,
        mode="ec2",
        exp_prefix=exp_tag,
        # python_command="/home/aboudy/anaconda2/envs/rllab-distributed/bin/python3.5"
        # plot=True,
    )