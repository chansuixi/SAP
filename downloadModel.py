from bert_serving.server.helper import  get_args_parser
from bert_serving.server import BertServer
import tensorflow as tf

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
args = get_args_parser().parse_args(['-model_dir', '/Users/yangkaixuan/Downloads/archive/saved_model.pb',
                                     '-pooling_strategy', 'NONE',
                                     '-max_seq_len','512'])
if __name__ == '__main__':
    server = BertServer(args)
    server.start()
# model_name = "bert_multi_cased_L-12_H-768_A-12"
#
# model = BertModel.from_pretrained(model_name)
#
# # 使用BertTokenizer类下载相应的tokenizer
# tokenizer = BertTokenizer.from_pretrained(model_name)