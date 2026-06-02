import sys  
sys.path.insert(0, 'mcp-servers')  
from llama_cpp import Llama  
from bridge.vision.minicpm import _get_model_path, _get_mmproj_path  
# Try to load mmproj alone to see if it's valid  
try:  
    mm = Llama(model_path=str(_get_mmproj_path()), n_ctx=512, verbose=False)  
    print('MMproj loaded as model: YES, type:', type(mm).__name__)  
    md = mm.metadata if hasattr(mm, 'metadata') else {}  
    for k,v in list(md.items())[:5]: print(k,v)  
except Exception as e:  
    print('Cannot load as model:', e)  
