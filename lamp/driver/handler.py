import digi
import digi.on as on
import digi.util as util

mock_gvr = "mock.digi.dev/v1/lamps"


# mock status
@on.mount
def do_mock_status(pv, mount):
    mock = get_mock(mount)
    power_attr, bright_attr = "control.power.status", "control.brightness.status"
    power = util.get(mock, f"spec.{power_attr}")
    bright = util.get(mock, f"spec.{bright_attr}")
    old_power, old_bright = util.get(pv, power_attr), \
                            util.get(pv, bright_attr)
    util.update(pv, power_attr, power)
    util.update(pv, bright_attr, bright)
    if power != old_power or bright != old_bright:
        report()


def get_mock(mount):
    mocks = mount.get(mock_gvr, {})
    assert len(mocks) <= 1, "at most one mock allowed"
    for _, mock in mocks.items():
        return mock
    return None


@on.control
def do_control(sv, meta, mount):
    bright_mode = meta.get("brightness")
    mock = get_mock(mount)

    # do mock lamp
    power = util.get(sv, "power.intent")
    if bright_mode == "auto":
        bright = digi.pool.query("avg(brightness)")
    else:
        bright = util.get(sv, "brightness.intent")

    # do other lamp
    ...

    util.update(mock, "spec.control.power.intent", power)
    util.update(mock, "spec.control.brightness.intent", bright)


def report():
    model = digi.rc.view()
    power, brightness = util.get(model, "control.power.status"), \
                        util.get(model, "control.brightness.status")
    wattage = util.get(model, "meta.wattage")
    watt = 0 if power != "on" or wattage is None else round(wattage * brightness, 1)
    digi.pool.load(
        [{
            "power": power,
            "brightness": brightness,
            "watt": watt,
        }]
    )


loader = util.Loader(load_fn=report)


@on.meta
def do_meta(meta):
    i = meta.get("report_interval", -1)
    if i < 0:
        digi.logger.info("Stop loader")
        loader.stop()
    else:
        loader.reset(i)
        loader.start()


if __name__ == '__main__':
    digi.run()
