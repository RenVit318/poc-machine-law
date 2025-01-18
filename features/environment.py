from service import Services


def before_scenario(context, scenario):
    context.services = Services()
    context.test_data = {}
    context.service_context = {}
    context.result = None


def after_scenario(context, scenario):
    pass
