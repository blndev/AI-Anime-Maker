from PIL import Image

images_by_group = {
    'male':
    {
        40:
        {
            'nosmile': Image.open("./unittests/testdata/face_male_age30_nosmile.jpg")
        }
    },
    'female':
    {
        20:
        {
            'nosmile': Image.open("./unittests/testdata/face_female_age20_nosmile.jpg"),
            'smile': Image.open("./unittests/testdata/face_female_age20_smile.jpg")
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
