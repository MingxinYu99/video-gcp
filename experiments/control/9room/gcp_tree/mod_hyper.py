import os.path

from blox import AttrDict
from gcp.infra.agent.benchmarking_agent import BenchmarkAgent
from gcp.infra.envs.miniworld_env.multiroom3d.multiroom3d_env import TopdownMultiroom3dEnv
from gcp.planning.cem_policy.cem_policy import ImageCEMPolicy
from gcp.planning.cem_policy.utils.sampler import ImageSequentialHierarchicalSampler
from gcp.planning.cem_policy.utils.cem_planner import HierarchicalImageCEMPlanner
from gcp.planning.cem_policy.utils.cost_fcn import ImageLearnedCostEstimate

from experiments.prediction.base_configs import gcp_tree as base_conf

BASE_DIR = '/'.join(str.split(__file__, '/')[:-1])
current_dir = os.path.dirname(os.path.realpath(__file__))

env_params = {
    'init_pos': None,
    'goal_pos': None,
    'n_rooms': 9,
    'heading_smoothing': 0.1,
    'crop_window': 40,
}

agent = AttrDict(
    type=BenchmarkAgent,
    env=(TopdownMultiroom3dEnv, env_params),
    T=200,
    image_height=32,
    image_width=32,
    start_goal_confs=os.environ['GCP_DATA_DIR'] + '/nav_9rooms/start_goal_configs/raw',
)

h_config = AttrDict(base_conf.model_config)
h_config.update({
    'state_dim': 2,
    'ngf': 16,
    'max_seq_len': 100,
    'hierarchy_levels':7,
    'nz_mid_lstm': 512,
    'n_lstm_layers': 3,
    'nz_mid': 128,
    'nz_enc': 128,
    'nz_vae': 256,
    'regress_length': True,
    'attach_state_regressor': True,
    'attach_inv_mdl': True,
    'inv_mdl_params': AttrDict(
        n_actions=2,
        use_convs=False,
        build_encoder=False,
    ),
    'decoder_distribution': 'discrete_logistic_mixture',
})
h_config.pop("add_weighted_pixel_copy")

cem_params = AttrDict(
    prune_final=True,
    horizon=100,
    action_dim=256,
    verbose=True,
    n_iters=3,
    batch_size=10,
    n_level_hierarchy=7,
    sampler=ImageSequentialHierarchicalSampler,
    sampling_rates_per_layer=[10, 10],
    cost_fcn=ImageLearnedCostEstimate,
    cost_config=AttrDict(
        checkpt_path=os.environ['GCP_EXP_DIR'] + '/prediction/9room/gcp_tree/weights'
    ),
)

policy = AttrDict(
    type=ImageCEMPolicy,
    params=h_config,
    checkpt_path=cem_params.cost_config.checkpt_path,
    cem_planner=HierarchicalImageCEMPlanner,
    cem_params=cem_params,
    replan_interval=agent.T+2,
    #load_epoch=10,
    closed_loop_execution=True
)

config = AttrDict(
    current_dir=current_dir,
    start_index=0,
    end_index=99,
    agent=agent,
    policy=policy,
    save_format=['raw'],
    data_save_dir=os.environ['GCP_EXP_DIR'] + '/control/nav_9rooms/gcp_tree',
    split_train_val_test=False,
    traj_per_file=1,
)
