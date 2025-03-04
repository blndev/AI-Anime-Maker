from PIL import Image

# TODO: need one image per group
images_by_group = {
    'male':
    {
        40:
        {
            'nosmile': Image.open("./unittests/testdata/face_male_age40_nosmile.jpg")
        },
        90:
        {
            'nosmile': Image.open("./unittests/testdata/face_male_age90_nosmile.jpg")
        }
    },
    'female':
    {
        20:
        {
            'nosmile': Image.open("./unittests/testdata/face_female_age20_nosmile.jpg"),
        },
        25:
        {
            'smile': Image.open("./unittests/testdata/face_female_age25_smile.jpg")
        },
        100:
        {
            'nosmile': Image.open("./unittests/testdata/face_female_age90_nosmile.jpg")
        },
        80:
        {
            'smile': Image.open("./unittests/testdata/face_female_age90_smile.jpg")
        }
    }


}

images = {}
for gender in images_by_group:
    for age in images_by_group[gender]:
        for expression in images_by_group[gender][age]:
            id = f"{gender}, age {age}, {expression}"
            image = images_by_group[gender][age][expression]
            images[id] = image
