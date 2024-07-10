import uuid
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader
from ops import *
from PIL import Image
from dataset import *


class Generator(nn.Module):
    
    def __init__(self, img_feat = 3, n_feats = 64, kernel_size = 3, num_block = 16, act = nn.PReLU(), scale=4):
        super(Generator, self).__init__()
        
        self.conv01 = conv(in_channel = img_feat, out_channel = n_feats, kernel_size = 9, BN = False, act = act)
        
        resblocks = [ResBlock(channels = n_feats, kernel_size = 3, act = act) for _ in range(num_block)]
        self.body = nn.Sequential(*resblocks)
        
        self.conv02 = conv(in_channel = n_feats, out_channel = n_feats, kernel_size = 3, BN = True, act = None)
        
        if(scale == 4):
            upsample_blocks = [Upsampler(channel = n_feats, kernel_size = 3, scale = 2, act = act) for _ in range(2)]
        else:
            upsample_blocks = [Upsampler(channel = n_feats, kernel_size = 3, scale = scale, act = act)]

        self.tail = nn.Sequential(*upsample_blocks)
        
        self.last_conv = conv(in_channel = n_feats, out_channel = img_feat, kernel_size = 3, BN = False, act = nn.Tanh())
        
    def forward(self, x):
        
        x = self.conv01(x)
        _skip_connection = x
        
        x = self.body(x)
        x = self.conv02(x)
        feat = x + _skip_connection
        
        x = self.tail(feat)
        x = self.last_conv(x)
        
        return x, feat


def EnhanceImage(image_path, 
              model='./model/preprocess/pre_trained_model_8000.pt', 
              num_workers=0, 
              res_num=16,
              output_dir='./result/'):
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = SingleImageData(image_path, in_memory = False, transform = None)
    loader = DataLoader(dataset, batch_size = 1, shuffle = False, num_workers = num_workers)
    
    generator = Generator(img_feat = 3, n_feats = 64, kernel_size = 3, num_block = res_num)
    generator.load_state_dict(torch.load(model, map_location=torch.device(device)))
    generator = generator.to(device)
    generator.eval()

    with torch.no_grad():
        for i, te_data in enumerate(loader):
            lr = te_data['LR'].to(device)
            output, _ = generator(lr)
            if torch.cuda.is_available():
                output = output[0].cuda().numpy()
            else:
                output = output[0].cpu().numpy()
            output = (output + 1.0) / 2.0
            output = output.transpose(1,2,0)
            result = Image.fromarray((output * 255.0).astype(np.uint8))
            filename = f"{uuid.uuid4()}.png"
            filepath = os.path.join(output_dir, filename)
            result.save(filepath)
            return filepath

def EnhancedImageGenerator(image_path, 
              model='./model/preprocess/pre_trained_model_8000.pt', 
              num_workers=0, 
              res_num=16,
              output_dir='./result/'):
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = SingleImageData(image_path, in_memory = False, transform = None)
    loader = DataLoader(dataset, batch_size = 1, shuffle = False, num_workers = num_workers)
    
    generator = Generator(img_feat = 3, n_feats = 64, kernel_size = 3, num_block = res_num)
    generator.load_state_dict(torch.load(model, map_location=torch.device(device)))
    generator = generator.to(device)
    generator.eval()

    with torch.no_grad():
        for i, te_data in enumerate(loader):
            lr = te_data['LR'].to(device)
            output, _ = generator(lr)
            if torch.cuda.is_available():
                output = output[0].cuda().numpy()
            else:
                output = output[0].cpu().numpy()
            output = (output + 1.0) / 2.0
            output = output.transpose(1,2,0)
            result = Image.fromarray((output * 255.0).astype(np.uint8))
            filename = f"{uuid.uuid4()}.png"
            filepath = os.path.join(output_dir, filename)
            result.save(filepath)
            return filepath

