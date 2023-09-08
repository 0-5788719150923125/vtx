from collections import defaultdict

subscribers = defaultdict(list)


def subscribe(event_type, fn, *args, **kwargs):
    for subscriber, _, _, _ in subscribers[event_type]:
        if subscriber == fn:
            return

    subscribers[event_type].append((fn, args, kwargs))


def post_event(event_type, *args, **kwargs):
    if event_type in subscribers:
        for fn, fn_args, fn_kwargs in subscribers[event_type]:
            fn(*args, *fn_args, **kwargs, **fn_kwargs)
