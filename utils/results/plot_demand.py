from __future__ import division

import matplotlib.pyplot as plt

plt.rc('text', usetex=True)
plt.rc('font', family='sans-serif', size=13)

# low, = plt.step([0, 900], [1/6, 1/6], linestyle='--', markevery=1, color='black', alpha=0.8)

# alt1, = plt.step([0, 300, 600, 900], [1/5, 1/5, 1/3, 7/15], linestyle='-.', color='dimgrey', marker='x', markevery=1, alpha=0.8)

# alt2, = plt.step([0, 300, 600, 900], [7/15, 7/15, 1/3, 1/5], linestyle=':', color='black', marker='+', markevery=1, alpha=0.8)

# plt.title('Demand Profile')

# plt.xticks([0, 300, 600, 900], [r'$0$', r'$300$', r'$600$', r'$900$'])
# plt.yticks([0, 5/30, 6/30, 10/30, 14/30], [r'$0$', r'$\frac{5}{30}$', r'$\frac{6}{30}$', r'$\frac{10}{30}$', r'$\frac{14}{30}$'])
# plt.xlabel('Time (seconds)')
# plt.ylabel('Proportion of Total Network Demand')
# plt.legend((low, alt1, alt2), (u"\u2663", u"\u2660", u"\u2666"))

# with open('/home/srishtid/Dropbox/Adaptive-Traffic-Signal-Control/IJCAI2019/Draft/images/wip/isolated-flow-legend.png', 'w') as fp:
#     plt.savefig(fp, dpi=300)

# plt.clf()

# plt.step([0, 900], [1/16, 1/16], linestyle='--', color='black', markevery=1, alpha=0.8) #, label=u"\u2666")

# plt.step([0, 900], [5/16, 5/16], linestyle='-', color='black', markevery=1, alpha=0.8) #, label=u"\u2663")

# plt.step([0, 300, 600, 900], [7/16, 7/16, 4/16, 1/16], linestyle='-.', marker='x', color='dimgrey', markevery=1, alpha=0.8) #, label=u"\u2660")

# plt.step([0, 300, 600, 900], [0, 0, 3/16, 6/16], linestyle=':', color='black', marker='+', markevery=1, alpha=0.8) #, label=u"\u2665")

# plt.title('Demand Profile')

# plt.xticks([0, 300, 600, 900], [r'$0$', r'$300$', r'$600$', r'$900$'])
# plt.yticks([0, 1/16, 2/16, 3/16, 4/16, 5/16, 6/16, 7/16], [r'$0$', r'$\frac{1}{16}$', r'$\frac{2}{16}$', r'$\frac{3}{16}$', r'$\frac{4}{16}$', r'$\frac{5}{16}$', r'$\frac{6}{16}$', r'$\frac{7}{16}$'])
# plt.xlabel('Time (seconds)')
# plt.ylabel('Proportion of Total Network Demand')
# # plt.legend()

# # plt.show()

# with open('/home/srishtid/Dropbox/Adaptive-Traffic-Signal-Control/IJCAI2019/Draft/images/wip/arterial-flow.png', 'w') as fp:
#     plt.savefig(fp, dpi=300)

# plt.clf()

plt.step([0, 900], [1/40, 1/40], linestyle='--', color='black', markevery=1, alpha=0.8) #, label=u"\u2605")

plt.step([0, 900], [3/40, 3/40], linestyle='-.', color='black', markevery=1, alpha=0.8) #, label=u"\u2663")

plt.step([0, 900], [5/40, 5/40], linestyle='-', color='black', markevery=1, alpha=0.8) #, label=u"\u2665")

plt.step([0, 300, 600, 900], [3.5/40, 3.5/40, 4/40, 4.5/40], linestyle='--', marker='x', color='black', markevery=1, alpha=0.8) #, label=u"\u2660")

plt.step([0, 300, 600, 900], [2.5/40, 2.5/40, 2/40, 1.5/40], linestyle=':', marker='+', color='black', markevery=1, alpha=1) #, label=u"\u2666")

# plt.title('Demand Profile')

plt.xticks([0, 300, 600, 900], [r'$0$', r'$300$', r'$600$', r'$900$'])
plt.yticks([0, 1/40, 2/40, 3/40, 4/40, 5/40], [r'$0$', r'$\frac{1}{40}$', r'$\frac{2}{40}$', r'$\frac{3}{40}$', r'$\frac{4}{40}$', r'$\frac{5}{40}$'])
plt.xlabel('Time (seconds)')
plt.ylabel('Proportion of Total Network Demand')
# plt.legend(loc='lower right', ncol=5, columnspacing=1.5, handletextpad=0.3)

# plt.show()

with open('/home/srishtid/Dropbox/Adaptive-Traffic-Signal-Control/IJCAI2019/Draft/images/wip/5x5-flow.png', 'w') as fp:
    plt.savefig(fp, dpi=300)