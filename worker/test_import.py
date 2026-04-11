import traceback
import sys

import sys
import torchvision.transforms.functional
sys.modules['torchvision.transforms.functional_tensor'] = torchvision.transforms.functional


try:
    import realesrgan
    from basicsr.archs.rrdbnet_arch import RRDBNet
    print('OK')
except Exception as e:
    traceback.print_exc()
