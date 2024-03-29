import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
from PIL import Image
from collections import OrderedDict


from app.pkg.settings import settings

from app.pkg.ml.try_on.preprocessing.humanparsing import networks
from app.pkg.ml.try_on.preprocessing.humanparsing.utils.transforms import get_affine_transform
from app.pkg.ml.try_on.preprocessing.humanparsing.utils.transforms import transform_logits

class HumanParsing:

    def __init__(self):
        
        self.WEIGHTS_PATH = f"{settings.ML.WEIGHTS_PATH}/human_parsing.pth"
  
        self.num_classes = 18
        self.input_size = [512, 512] # this will be made in pipeline. No need extra resize 
        self.label = ['Background', 'Hat', 'Hair', 'Sunglasses', 'Upper-clothes', 'Skirt', 'Pants', 'Dress', 'Belt',
                  'Left-shoe', 'Right-shoe', 'Face', 'Left-leg', 'Right-leg', 'Left-arm', 'Right-arm', 'Bag', 'Scarf']



        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.406, 0.456, 0.485], std=[0.225, 0.224, 0.229])
        ])
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.setup()



    def setup(self):
        self.model = networks.init_model('resnet101', num_classes=self.num_classes, pretrained=None)
        state_dict = torch.load(self.WEIGHTS_PATH)['state_dict']
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:]  # remove `module.`
            new_state_dict[name] = v
        self.model.load_state_dict(new_state_dict)
        self.model.to(device=self.device)
        self.model.eval()

    def __call__(self, pil_image:Image,):
        """
        pil_image - pil image
        """
        image = np.array(pil_image)[:,:,::-1].copy()
        #image = cv2.imread(input_path)
        # if image is None:
        #     raise Exception(f"Image {input_path} is not found for pose estimation")
        assert image.shape == (512, 384, 3)

        
        dataset = SingleImageDataset(pil_image,
                                     input_size=self.input_size,
                                     transform=self.transform)
        dataloader = DataLoader(dataset)

        # if not os.path.exists(args.output_dir):
        #     os.makedirs(args.output_dir)

        palette = get_palette(self.num_classes)
        with torch.no_grad():
            for idx, batch in enumerate(dataloader):
                image, meta = batch
                # img_name = meta['name'][0]
                c = meta['center'].numpy()[0]
                s = meta['scale'].numpy()[0]
                w = meta['width'].numpy()[0]
                h = meta['height'].numpy()[0]

                output = self.model(image.cuda())
                upsample = torch.nn.Upsample(size=self.input_size, mode='bilinear', align_corners=True)
                upsample_output = upsample(output[0][-1][0].unsqueeze(0))
                upsample_output = upsample_output.squeeze()
                upsample_output = upsample_output.permute(1, 2, 0)  # CHW -> HWC

                logits_result = transform_logits(upsample_output.data.cpu().numpy(),
                                                 c, s, w, h,
                                                 input_size=self.input_size)
                parsing_result = np.argmax(logits_result, axis=2)
                output_img = Image.fromarray(np.asarray(parsing_result, dtype=np.uint8))
                output_img.putpalette(palette)
                return output_img



class SingleImageDataset:
    def __init__(self, pil_image, input_size=[512, 512], transform=None):
        self.image = np.array(pil_image)[:,:,::-1] 
        
        self.input_size = input_size
        self.transform = transform
        self.aspect_ratio = input_size[1] * 1.0 / input_size[0]
        self.input_size = np.asarray(input_size)

#        self.file_list = [self.fp]

    def __len__(self):
        return 1  # len(self.file_list)

    def _box2cs(self, box):
        x, y, w, h = box[:4]
        return self._xywh2cs(x, y, w, h)

    def _xywh2cs(self, x, y, w, h):
        center = np.zeros((2), dtype=np.float32)
        center[0] = x + w * 0.5
        center[1] = y + h * 0.5
        if w > self.aspect_ratio * h:
            h = w * 1.0 / self.aspect_ratio
        elif w < self.aspect_ratio * h:
            w = h * self.aspect_ratio
        scale = np.array([w, h], dtype=np.float32)
        return center, scale

    def __getitem__(self, index):
        img = self.image
        h, w, _ = img.shape

        # Get person center and scale
        person_center, s = self._box2cs([0, 0, w - 1, h - 1])
        r = 0
        trans = get_affine_transform(person_center, s, r, self.input_size)
        input = cv2.warpAffine(
            img,
            trans,
            (int(self.input_size[1]), int(self.input_size[0])),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0))

        input = self.transform(input)
        meta = {
           # 'name': self.fp,
            'center': person_center,
            'height': h,
            'width': w,
            'scale': s,
            'rotation': r
        }

        return input, meta


def get_palette(num_cls):
    """ Returns the color map for visualizing the segmentation mask.
    Args:
        num_cls: Number of classes
    Returns:
        The color map
    """
    n = num_cls
    palette = [0] * (n * 3)
    for j in range(0, n):
        lab = j
        palette[j * 3 + 0] = 0
        palette[j * 3 + 1] = 0
        palette[j * 3 + 2] = 0
        i = 0
        while lab:
            palette[j * 3 + 0] |= (((lab >> 0) & 1) << (7 - i))
            palette[j * 3 + 1] |= (((lab >> 1) & 1) << (7 - i))
            palette[j * 3 + 2] |= (((lab >> 2) & 1) << (7 - i))
            i += 1
            lab >>= 3
    return palette


      #  cv2.imwrite(output_path,canvas)

# if __name__ == '__main__':
#     hp = HumanParsing()
#     hp(
#        "/usr/src/app/volume/data/resized/resized_human.png",
#        "/usr/src/app/volume/data/parsed/parsed_human.png",
#        )
    


