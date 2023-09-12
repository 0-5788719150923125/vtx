from collections import defaultdict
import asyncio

subscribers = defaultdict(list)


def subscribe_event(event_type, fn, *args, **kwargs):
    for subscriber, _, _ in subscribers[event_type]:
        if subscriber == fn:
            return

    subscribers[event_type].append((fn, args, kwargs))


async def run_async_event_handlers(event_type, *args, **kwargs):
    async_functions = []

    for fn, fn_args, fn_kwargs in subscribers[event_type]:
        if asyncio.iscoroutinefunction(fn):
            async_functions.append(fn(*args, *fn_args, **kwargs, **fn_kwargs))
        else:
            fn(*args, *fn_args, **kwargs, **fn_kwargs)

    await asyncio.gather(*async_functions)


def post_event(event_type, *args, **kwargs):
    if event_type in subscribers:
        loop = asyncio.get_event_loop()

        if loop.is_running():
            # If the event loop is already running, use create_task
            asyncio.create_task(run_async_event_handlers(event_type, *args, **kwargs))
        else:
            # If the event loop is not running, run it manually
            loop.run_until_complete(
                run_async_event_handlers(event_type, *args, **kwargs)
            )
