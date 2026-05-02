from src.char.BaseChar import Priority

START_CHANGLI_BURST = "start_changli_burst"
START_VERINA_FULL = "start_verina_full"
START_JINHSI_ECHO = "start_jinhsi_echo"
START_CHANGLI_COMBO = "start_changli_combo"
START_VERINA_LIGHT = "start_verina_light"
START_JINHSI_NO_ECHO = "start_jinhsi_no_echo"
LOOP_CHANGLI = "loop_changli"
LOOP_VERINA = "loop_verina"
LOOP_JINHSI_ECHO = "loop_jinhsi_echo"
LOOP_JINHSI_NO_ECHO = "loop_jinhsi_no_echo"

STATE_ATTR = "_dragon_phoenix_state"
TEAM_SIGNATURE = ("Jinhsi", "Changli", "Verina")

PHASE_OWNER = {
    START_CHANGLI_BURST: "Changli",
    START_VERINA_FULL: "Verina",
    START_JINHSI_ECHO: "Jinhsi",
    START_CHANGLI_COMBO: "Changli",
    START_VERINA_LIGHT: "Verina",
    START_JINHSI_NO_ECHO: "Jinhsi",
    LOOP_CHANGLI: "Changli",
    LOOP_VERINA: "Verina",
    LOOP_JINHSI_ECHO: "Jinhsi",
    LOOP_JINHSI_NO_ECHO: "Jinhsi",
}


def is_team(task):
    """严格匹配 1 今汐、2 长离、3 维里奈的龙凤维站位。"""
    chars = getattr(task, "chars", [])
    if len(chars) < 3:
        return False
    for index, class_name in enumerate(TEAM_SIGNATURE):
        char = chars[index]
        if char is None or char.__class__.__name__ != class_name or char.index != index:
            return False
    return True


def get_state(task):
    """读取龙凤维手法状态；队伍不匹配时清掉旧状态。"""
    if not is_team(task):
        reset(task)
        return None
    state = getattr(task, STATE_ATTR, None)
    if not state:
        state = {
            "phase": START_CHANGLI_BURST,
            "jinhsi_echo_next": True,
        }
        setattr(task, STATE_ATTR, state)
    return state


def reset(task):
    """战斗结束或队伍变化时移除龙凤维手法进度。"""
    if hasattr(task, STATE_ATTR):
        delattr(task, STATE_ATTR)


def active(task):
    """判断当前任务是否可以使用龙凤维专用连招。"""
    return get_state(task) is not None


def phase_for(char):
    """返回当前角色需要执行的龙凤维阶段。"""
    state = get_state(char.task)
    if state is None:
        return None
    phase = state["phase"]
    if PHASE_OWNER.get(phase) == char.__class__.__name__:
        return phase
    return None


def should_yield(char):
    """当前角色不是手法阶段目标时交还切人逻辑。"""
    state = get_state(char.task)
    if state is None:
        return False
    return PHASE_OWNER.get(state["phase"]) != char.__class__.__name__


def priority_for(char, current_char):
    """为龙凤维当前阶段目标提供最高切人评分。"""
    state = get_state(char.task)
    if state is None:
        return None
    owner = PHASE_OWNER.get(state["phase"])
    if char.__class__.__name__ == owner and char != current_char:
        return Priority.MAX
    if char != current_char:
        return Priority.MIN
    return None


def complete(task):
    """根据手法表推进龙凤维阶段。"""
    state = get_state(task)
    if state is None:
        return None
    phase = state["phase"]
    if phase == START_CHANGLI_BURST:
        state["phase"] = START_VERINA_FULL
    elif phase == START_VERINA_FULL:
        state["phase"] = START_JINHSI_ECHO
    elif phase == START_JINHSI_ECHO:
        state["phase"] = START_CHANGLI_COMBO
    elif phase == START_CHANGLI_COMBO:
        state["phase"] = START_VERINA_LIGHT
    elif phase == START_VERINA_LIGHT:
        state["phase"] = START_JINHSI_NO_ECHO
    elif phase == START_JINHSI_NO_ECHO:
        state["jinhsi_echo_next"] = True
        state["phase"] = LOOP_CHANGLI
    elif phase == LOOP_CHANGLI:
        state["phase"] = LOOP_VERINA
    elif phase == LOOP_VERINA:
        state["phase"] = LOOP_JINHSI_ECHO if state["jinhsi_echo_next"] else LOOP_JINHSI_NO_ECHO
    elif phase == LOOP_JINHSI_ECHO:
        state["jinhsi_echo_next"] = False
        state["phase"] = LOOP_CHANGLI
    elif phase == LOOP_JINHSI_NO_ECHO:
        state["jinhsi_echo_next"] = True
        state["phase"] = LOOP_CHANGLI
    return state["phase"]


def tap_attack(char, count, interval=0.16):
    """按手法表执行固定次数普攻。"""
    for _ in range(count):
        char.click()
        char.sleep(interval)


def cast_resonance(char, post_sleep=0.12, has_animation=False, time_out=1.4):
    """释放共鸣技能；技能未点亮时仍发送按键尝试。"""
    if char.resonance_available():
        return char.click_resonance(
            post_sleep=post_sleep,
            has_animation=has_animation,
            send_click=False,
            animation_min_duration=0.2 if has_animation else 0,
            time_out=time_out,
        )[0]
    char.send_resonance_key(post_sleep=post_sleep)
    return False


def cast_echo(char, post_sleep=0.12):
    """释放声骸技能；冷却状态下发送按键兜底。"""
    if char.echo_available():
        return char.click_echo(time_out=0)
    char.send_echo_key(after_sleep=post_sleep)
    return False


def cast_liberation(char, send_click=False):
    """释放共鸣解放；技能可用时等待动画回到队伍界面。"""
    if char.liberation_available():
        return char.click_liberation(send_click=send_click, wait_if_cd_ready=0)
    return False
