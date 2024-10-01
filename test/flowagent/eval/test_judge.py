from flowagent import Config, DataManager, Judger

if __name__ == '__main__':
    cfg = Config.from_yaml(DataManager.normalize_config_name('default.yaml'))
    cfg.exp_version = "240819_01"
    cfg.user_profile_id = 0

    judge = Judger(cfg)
    out = judge.start_judge()
    print(out)