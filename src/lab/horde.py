import asyncio
import os

# from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
# from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGeneration

# from stablehorde_api import GenerationInput, ModelGenerationInputStable, StableHordeAPI
# from pydantic.functional_validators import field_validator


def main(config):
    asyncio.run(generate())


async def generate():
    pass
    # simple_client = AIHordeAPISimpleClient()

    # generations: list[ImageGeneration] = simple_client.image_generate_request(
    #     ImageGenerateAsyncRequest(
    #         apikey=key,
    #         prompt="masterpiece, best quality, ((Yang Xueguo)), leviathan creature, terrifying",
    #         models=["Deliberate"],
    #     ),
    # )
    # print(generations[0])
    # image = simple_client.generation_to_image(generations[0])
    # print(image)

    # image.save("/src/one.webp")

    # key = os.environ["STABLE_HORDE_API_KEY"]
    # client = StableHordeAPI(key)
    # payload = GenerationInput(
    #     "masterpiece, best quality, ((Yang Xueguo)), leviathan creature, terrifying",
    #     # params=ModelGenerationInputStable(
    #     #     height=512, width=768, steps=50, post_processing=["RealESRGAN_x4plus"]
    #     # ),
    #     # height=512,
    #     nsfw=True,
    #     censor_nsfw=False,
    #     models=["Anything Diffusion"],
    #     # n=1,
    # )
    # # payload can also be a dict, which is useful, if something new added
    # txt2img_rsp = await client.txt2img_request(payload)
    # img_uuid = txt2img_rsp.id

    # done = False
    # while not done:
    #     # Checking every second if image is generated
    #     await asyncio.sleep(15)
    #     generate_check = await client.generate_check(img_uuid)
    #     if generate_check.done == 1:
    #         done = True

    # # Generating a status which has all generations (in our case,
    # # there should be 5 generations, because n is set to 5)
    # generate_status = await client.generate_status(img_uuid)
    # generations = generate_status.generations
    # print(generations[0].img)


if __name__ == "__main__":
    main()
