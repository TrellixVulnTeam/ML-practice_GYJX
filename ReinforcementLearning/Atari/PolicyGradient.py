import gym 
import tensorflow as tf
import numpy as np
import os

try:
    tf = tf.compat.v1
    tf.disable_eager_execution()
except ImportError:
    pass

def conv2d(X, channel_no = 64, kernel_size = 3, stride_no = 1):
    return tf.layers.conv2d(X, channel_no, 
                               [kernel_size, kernel_size], 
                               [stride_no, stride_no], 
                               padding='SAME', 
                               kernel_initializer=tf.keras.initializers.glorot_normal,
                               activation=tf.nn.relu
                               )
pass

def Q(S):
    S = (tf.cast(S,tf.float32)-128)/128.  #(210, 160, 3)
    #S = tf.layers.Dropout(.5)(S)
    S = tf.layers.conv2d(S,16, [1,1], [1,1], padding='SAME', activation=tf.nn.relu)
    conv1 = conv2d(S, stride_no=2) #(105, 80)
    #conv1 = tf.layers.Dropout(.5)(conv1)
    conv2 = conv2d(conv1, stride_no=2) #(53, 40)
    #conv2 = tf.layers.Dropout(.5)(conv2)
    conv3 = conv2d(conv2, stride_no=2) #(27, 20)
    #conv3 = tf.layers.Dropout(.5)(conv3)
    conv4 = conv2d(conv3, 128, stride_no=2) #(14, 10)
    #conv4 = tf.layers.Dropout(.5)(conv4)
    conv5 = conv2d(conv4, 256, stride_no=2) #(7, 5)
    #conv5 = tf.layers.Dropout(.5)(conv5)
    conv6 = conv2d(conv5, 512, stride_no=2) #(4, 3)
    #conv6 = tf.layers.Dropout(.5)(conv6)
    
    f1 = tf.layers.flatten(conv6)
    #f1 = tf.layers.Dropout(.5)(f1)
    f2 = tf.layers.dense(f1, 1024, activation=tf.nn.relu)
    #f2 = tf.layers.Dropout(.5)(f2)
    f3 = tf.layers.dense(f2, 512, activation=tf.nn.relu)
    out = tf.layers.dense(f3, 4)

    return out
pass

# Enviroment settings
STEP_LIMIT = 1000
EPISODE = 1000
EPSILONE = .8
REWARD_b = .0
REWARD_NORMA = 500 # because the peak reward is close to 500, empiritically
GAMMA = .5
ALPHA = .9
DIE_PANELTY = 0
WARMING_EPI = 0
BEST_REC = 0.
BEST_STEPS = 1.
STATE_GAMMA = .9

env = gym.make('SpaceInvaders-v0') 
os.system("echo > score_rec.txt") #clean the previoud recorders

# Actor settings
#Opt_size = 32
Act_S = tf.placeholder(tf.int8, [None, 210, 160, 3])
Act_R = tf.placeholder(tf.float32, [None])
Actions4Act = tf.placeholder(tf.uint8, [None])
Actions4Act_oh = tf.one_hot(Actions4Act, 4) 

Act_A = Q(Act_S)
Command_A = tf.argmax(tf.nn.softmax(Act_A), axis=-1)

# PL = Act_R * -tf.log(tf.reduce_sum(tf.nn.softmax(Act_A) * Actions4Act_oh)+1E-9)
PL = (Act_R) * tf.nn.softmax_cross_entropy_with_logits(labels=Actions4Act_oh, logits=Act_A)

#Opt = tf.train.RMSPropOptimizer(1E-4, .6, momentum=.9, centered=False).minimize(PL)
#Opt = tf.train.MomentumOptimizer(learning_rate=1E-6, momentum=.8).minimize(PL)

optimizer = tf.train.RMSPropOptimizer(1E-4, .6, momentum=.9, centered=False)
gvs = optimizer.compute_gradients(PL)
capped_gvs = [(tf.clip_by_value(grad, -.5, .5), var) for grad, var in gvs]
Opt = optimizer.apply_gradients(capped_gvs)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

episode = 0
while(1):
    episode += 1
    Rp = 0.
    S = env.reset() #(210, 160, 3)
    GameScore = 0
    Clives = 3
    Reward_cnt = 0.
    CuReward = 0.
    R_list, S_list = [],[]
    
    steps = 0
    if (np.random.random() >= EPSILONE/np.clip(episode-WARMING_EPI,1E-9,None)) or (WARMING_EPI < episode) :
        Greedy_flag = False 
    else:
        Greedy_flag = True 
    pass
    while(1):
        steps += 1
    # for step in range(STEP_LIMIT):
        #env.render() # show the windows. If you don't need to monitor the state, just comment this.
        # print(S)
        
        # A = env.action_space.sample() # random sampling the actions
        # print(A)

        # sampling action from Q
        # epsilon greedy
        # actions: [noop, fire, right, left, right fire, left fire] 
        if Greedy_flag or (np.random.random() < .2):
            A = np.random.randint(4) # exlude right fire and left fire, such combo actions
        else:
            A = sess.run(Command_A, feed_dict={Act_S:np.array(S).reshape([1, 210, 160, 3])})[0]
        pass
        # print(A) # monitor the action

        Sp = S.copy()
        S, R, finish_flag, info = env.step(A)
        GameScore += R
        S = (Sp * STATE_GAMMA + S) * .5  # keep the previoud state as input would be creating a RNN like condition
        if A in [0]:
            R += REWARD_b * .8 # give the reward for moving. This would be helpful for telling agent to avopod bullet
        elif A in [2,3]:
            R += REWARD_b * 1.
        pass
        
        # advantage, Q
        # Reward_cnt = GAMMA * pow((R - Rp),2)  # advantage, Q
        Reward_cnt = GAMMA * (Rp - R)  
        
        Rp = R 
        #print(R)

        # CuReward = CuReward * GAMMA + R
        CuReward = ALPHA * CuReward + Reward_cnt
        # CuReward += Reward_cnt
        # CuReward = CuReward * GAMMA + Reward_cnt
        # CuReward = CuReward * GAMMA + (Reward_cnt - (BEST_REC/BEST_STEPS))
        #print(CuReward)

        # print('Reward:{}'.format(R)) # the reward will give this action will get how much scores. it's descreted.
        # print('Info:{}'.format(info['ale.lives'])) # info in space invader will give the lives of the current state

        if finish_flag or (Clives > info['ale.lives']):
            Clives = info['ale.lives']
            # Rp -= DIE_PANELTY - CuReward 
            # CuReward += Rp
            CuReward = 0
            # CuReward = np.clip(CuReward, 0, None)
            # print('This episode is finished ...')
            Loss, _ = sess.run([PL, Opt], 
                               feed_dict={
                                          Act_S:np.array(Sp).reshape([-1, 210, 160, 3]),
                                          Act_R:np.array(CuReward).reshape([-1]),
                                          Actions4Act:np.array(0).reshape([-1])
                                         }
                               )             
            if finish_flag:
                if BEST_REC < GameScore:
                    BEST_REC = GameScore 
                pass
                if BEST_STEPS < steps:
                    BEST_STEPS = steps 
                pass
                if REWARD_b < (GameScore/steps) :
                    REWARD_b = (GameScore/steps)
                pass 
                if DIE_PANELTY < CuReward:
                    DIE_PANELTY = CuReward * .8 
                    #print(DIE_PANELTY)
                pass
                os.system("echo {} >> score_rec.txt".format(GameScore))
                break
            else:
                continue
            pass
        pass 
        # TD
        Loss, _ = sess.run([PL, Opt], 
                            feed_dict={
                                    Act_S:np.array(Sp).reshape([-1, 210, 160, 3]),
                                    Act_R:np.array(CuReward).reshape([-1]),
                                    Actions4Act:np.array(A).reshape([-1])
                                    }
                            )
        #print('Action:{}  Loss:{} Epsilon:{} greedy:{} score:{}'.format(A, Loss, EPSILONE/np.clip(episode-WARMING_EPI,1E-9,None), Greedy_flag, GameScore))

    pass
    print("Epi:{}  Score:{}  Loss:{}  Reward:{}".format(episode,GameScore,Loss,CuReward))


pass
