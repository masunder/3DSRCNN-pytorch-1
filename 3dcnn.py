import argparse, os

import h5py
import torch.backends.cudnn as cudnn
import torch.nn as nn
import torch.optim as optim
import random
import time
from torch.utils.data import DataLoader
from model import Net
from dataset import DatasetFromHdf5

# Training settings
parser = argparse.ArgumentParser(description="Pytorch 3DSRCNN")
parser.add_argument("--batchSize", type=int, default=64, help="Training batch size")
parser.add_argument("--start-epoch", default=1, type=int, help="Manual epoch number (useful on restarts)")
parser.add_argument("--nEpochs", type=int, default=10, help="Number of epochs to train for")
parser.add_argument("--lr", type=float, default=0.1, help="Learning Rate. Default=0.1")
parser.add_argument("--step", type=int, default=10, help="Sets the learning rate to the initial LR decayed by momentum every n epochs, Default: n=10")
parser.add_argument("--clip", type=float, default=0.4, help="Clipping Gradients. Default=0.4")
parser.add_argument("--threads", type=int, default=0, help="Number of threads for data loader to use, Default: 1")
parser.add_argument("--momentum", default=0.9, type=float, help="Momentum, Default: 0.9")
parser.add_argument("--weight-decay", "--wd", default=1e-4, type=float, help="Weight decay, Default: 1e-4")
parser.add_argument('--train_path',type=str,default="train_data/3dtrain.h5",help='Path to train dataset')
parser.add_argument('--memo', default= 'L_', type=str, help='prefix of logger ')


def main():
    global opt, model
    opt = parser.parse_args()
    print(opt)

    # Sets the seed for generating random numbers to a non-deterministic random number.
    opt.seed = random.randint(1, 10000)
    print("Random Seed: ", opt.seed)
    torch.manual_seed(opt.seed)

    # This flag allows you to enable the inbuilt cudnn auto-tuner
    # to find the best algorithm to use for your hardware.
    cudnn.benchmark = True

    # Loading datasets
    print("===> Loading datasets")
    train_set = DatasetFromHdf5(opt.train_path)
    training_data_loader = DataLoader(dataset=train_set, num_workers=opt.threads, batch_size=opt.batchSize,
                                      shuffle=True)

    # Building model
    print("===> Building model")
    model = Net(2)

    criterion = nn.SmoothL1Loss()

    print("===> Setting Optimizer")
    #TODO
    # for i in model.parameters():
    #     print(i.grad)
    optimizer = optim.SGD(model.parameters(), lr=opt.lr, momentum=opt.momentum, weight_decay=opt.weight_decay)

    print("===> Training")
    model_saved_prefix = get_time_stamp(time) + opt.memo + "_model"
    saved_model_path = os.path.join("model/", model_saved_prefix)
    for epoch in range(opt.start_epoch, opt.nEpochs + 1):
        train(training_data_loader, optimizer, model, criterion, epoch)
        save_checkpoint(model, epoch, saved_model_path)


def adjust_learning_rate(optimizer, epoch):
    """Sets the learning rate to the initial LR decayed by 10 every 10 epochs"""
    lr = opt.lr * (0.1 ** (epoch // opt.step))
#    lr=0.01
    return lr


def train(training_data_loader, optimizer, model, criterion, epoch):
    lr = adjust_learning_rate(optimizer, epoch - 1)

    for param_group in optimizer.param_groups:
        param_group["lr"] = lr

    print("Epoch={}, lr={}".format(epoch, optimizer.param_groups[0]["lr"]))

    model.train()  # model设为Train模式
    iteration_100_count = 0
    for iteration, batch in enumerate(training_data_loader, 1):
        print(iteration)
        input, target = batch[0], batch[1]  # 因为是target设为false
        input = input.unsqueeze(1)
        target = target.unsqueeze(1)
        #        print('input size:',input.shape)
        pre = time.time()
        loss = criterion(model(input), target)
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), opt.clip)
        optimizer.step()
        consume_time = time.time() - pre
        iteration_100_count += consume_time
        if iteration == len(training_data_loader):
            print("===> Epoch[{}]({}/{}): Loss: {:.10f},consume time:{}".format(epoch, iteration,
                                                                                len(training_data_loader),
                                                                                loss.data.item(), iteration_100_count))
            iteration_100_count = 0
        if iteration % 100 == 0:
            # for net in model.parameters():
            #     print(net.grad)
            print("===> Epoch[{}]({}/{}): Loss: {:.10f},consume time:{}".format(epoch, iteration,
                                                                                len(training_data_loader),
                                                                                loss.data.item(), iteration_100_count))
            iteration_100_count = 0


def save_checkpoint(model, epoch, saved_path="model/"):
    model_out_path = os.path.join(saved_path, "model_epoch_{}.pkl".format(epoch))
    state = {"epoch": epoch, "model": model}
    if not os.path.exists(saved_path):
        os.makedirs(saved_path)

    torch.save(state, model_out_path)

    print("=========Checkpoint saved to {}".format(model_out_path))


def get_time_stamp(time):
    timeStamp = time.strftime("%m%d-%H%M", time.localtime(time.time()))
    return timeStamp


if __name__ == "__main__":
    import torch

    os.environ["CUDA_VISIBLE_DEVICES"] = ' 3 '

    main()
