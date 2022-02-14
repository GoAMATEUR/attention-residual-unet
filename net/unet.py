"""
    By:     Hsy
    Date:   2022/1/29
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from net.vgg import VGG
from net.resnet import ResNet


class UpSampBlock(nn.Module):
    def __init__(self, in_channel, out_channel, dropout_rate=0.2):
        super(UpSampBlock, self).__init__()
        self.convLayers = nn.Sequential(
            nn.Conv2d(2*out_channel, out_channel, 3, 1, 1, padding_mode='reflect', bias=False),
            nn.BatchNorm2d(out_channel),
            nn.Dropout2d(dropout_rate),
            nn.LeakyReLU(),
            nn.Conv2d(out_channel, out_channel, 3, 1, 1, padding_mode='reflect', bias=False),
            nn.Dropout2d(dropout_rate),
            nn.LeakyReLU(),
        )
        self.reduceLayers = nn.Sequential(
            nn.Conv2d(in_channel, out_channel, 1, 1)
        )
           
    def forward(self, input, feature): # feature a*a*b, input: a/2 * a/2 * 2b
        """
        in_channel = 2*out_channel
        
        Args:
            input: from layer below (batch_size, in_channel, H/2, W/2)
            feature: feature from parallel dSamp layer (batch_size, out_channel, H, W)
        """
        interpolated = F.interpolate(input, scale_factor=2, mode='nearest') # (in_channel, H, W)
        output = self.reduceLayers(interpolated)#(out_channel, H, W)
        output = torch.cat((output, feature), dim = 1) # a*a*2b
        return self.convLayers(output)#a*a*b
    
class UNet(nn.Module):
    """[summary]

    Args:
        nn ([type]): [description]
    """
    def __init__(self, backbone_type: str, is_train: bool = True, drop_rate: float = 0.3):
        super(UNet, self).__init__()
        # backbone: VGG16/ResNet50
        if is_train:
            self.dropRate = drop_rate
            self.is_onehot = False
        else:
            self.dropRate = 0
            self.is_onehot = True
            
                 
        if backbone_type == "VGG16":
            self.backbone = VGG()
            self.downList = [64, 128, 256, 512, 1024]
        elif backbone_type == "ResNet50":
            self.backbone = ResNet()
            self.downList = [64, 256, 512, 1024, 2048]
        else:
            raise("Invalid type")
        
        # Up Sampling Blocks
        
        
        self.upSamp1 = UpSampBlock(self.downList[-1], self.downList[-2], self.dropRate)
        self.upSamp2 = UpSampBlock(self.downList[-2], self.downList[-3], self.dropRate)
        self.upSamp3 = UpSampBlock(self.downList[-3], self.downList[-4], self.dropRate)
        self.upSamp4 = UpSampBlock(self.downList[-4], self.downList[-5], self.dropRate)
        
        # Generate final output
        self.outBlock = nn.Sequential(
            nn.Conv2d(self.downList[0], 1, 3, 1, padding=1),
            nn.Sigmoid() # activation
        )
          
        
    def forward(self, input):

        f1, f2, f3, f4, f5 = self.backbone(input)
        
        out = self.upSamp1(f5, f4)
        out = self.upSamp2(out, f3)
        out = self.upSamp3(out, f2)
        out = self.upSamp4(out, f1)
        out = self.outBlock(out)
        if self.is_onehot:
            out = out > 0.5
            out = out.float()
        
        return out
    
if __name__ == "__main__":
    pass
    
    
        