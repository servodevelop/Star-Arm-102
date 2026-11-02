"""常用阻尼默认值。网页已保存的参数优先；修改策略数组后需同步绑定配置的 policy。"""

DEFAULT_POWER_MW = 1200
# 网页各轴默认上限，顺序：J1、J2、J3、J4、J5、J6、夹爪。0 表示关闭普通阻尼。
JOINT_POWER_MW = [1200, 1200, 1200, 1200, 1200, 1200, 1200]
HOLD_POWER_MW = 1500

# 同样按七轴排列；单位 Nm。死区越小越灵敏，满输出标尺越小输出越强。
DEADZONE_NM = [.7, 1., 1., .6, .35, .35, .35]
MOVING_MARGIN_NM = [.15, .4, .6, .2, .15, .15, .08]
EXCESS_FULL_SCALE_NM = [1., 3., 5., 3., 1., 1., .25]

RESIDUAL_FILTER_S = .12
CONFIRMATION_S = .10
POWER_FILTER_S = .06
POWER_RISE_MW_S = 5000.
POWER_FALL_MW_S = 10000.
