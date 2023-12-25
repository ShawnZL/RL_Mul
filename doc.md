# features

1. `log(message)` 函数：
   - 该函数用于输出带有时间戳的日志消息。日志消息包括当前时间、"DRiLLS" 标识和传递的消息。
2. `yosys_stats(design_file, yosys_binary, stats)` 函数：
   - 该函数通过调用 Yosys 工具获取电路设计文件的统计信息。
   - 使用 `check_output` 调用 Yosys，执行命令 "read_verilog \<design_file\>; stat"。
   - 解析 Yosys 输出，提取电路的一些统计数据，包括电路中的门数量、电线数量、与门（AND）、或门（OR）、非门（NOT）的数量等。
   - 返回一个字典（stats）包含了提取的统计信息。
3. `abc_stats(design_file, abc_binary, stats)` 函数：
   - 该函数通过调用 ABC 工具获取电路设计文件的统计信息。
   - 使用 `check_output` 调用 ABC，执行命令 "read_verilog \<design_file\>; print_stats"。
   - 解析 ABC 输出，提取电路的一些统计数据，包括输入输出引脚数量、电路中的边数量、层级数量、锁存器（latches）数量等。
   - 返回一个字典（stats）包含了提取的统计信息。
4. `extract_features(design_file, yosys_binary='yosys', abc_binary='abc')` 函数：
   - 该函数是主函数，用于提取电路设计文件的特征。
   - 创建了两个子进程分别调用 `yosys_stats` 和 `abc_stats` 函数，每个子进程获取部分统计信息。
   - 主进程等待两个子进程完成，并将它们获取的统计信息整合成一个包含多个特征的 NumPy 数组。
   - 返回特征数组，包括输入输出引脚数量、节点数量、边数量、层级数量、锁存器数量以及不同门类型的百分比。

# scl_session

这是一个用于逻辑综合优化的 Python 类，主要使用 ABC 工具。以下是对其中一些重要方法和属性的解释：

1. `log(message)` 函数：
   - 用于输出带有时间戳的日志消息。

2. `SCLSession` 类：
   - 表示逻辑综合优化会话的类。
   - `__init__(self, params)`：初始化函数，接收参数并设置一些初始状态，包括动作空间长度、观察空间大小等。
   - `reset(self)`：重置环境状态，创建一个新的优化实验，并返回初始状态。
   - `step(self, optimization)`：接收一个优化索引

并返回新的状态、奖励、是否完成等信息。

3. `_run(self)` 方法：
   - 运行 ABC 工具，执行一系列命令，获取优化后的电路设计文件。
   - 更新环境状态，包括迭代次数、延迟、面积等。
   - 返回新的电路状态和奖励。

4. `_get_metrics(self, stats)` 方法：
   - 从 ABC 统计命令的输出中解析延迟和面积。

5. `_get_reward(self, delay, area)` 方法：
   - 根据延迟、面积、约束等计算奖励。

6. `_reward_table(self, constraint_met, contraint_improvement, optimization_improvement)` 方法：
   - 返回奖励表格中的奖励值。

7. `_get_state(self, design_file)` 方法：
   - 利用 Yosys 工具从设计文件中提取特征，返回状态。

该类的实例用于在逻辑综合优化环境中执行操作、获取奖励，并模拟优化过程。

这部分代码定义了一个计算奖励的方法 `_get_reward` 和一个奖励表 `_reward_table`。在强化学习中，奖励是算法优化的目标，通过奖励的反馈来指导算法学习出适应环境的策略。

首先，方法 `_get_reward` 接受两个参数 `delay` 和 `area`，表示当前电路的时延和面积。然后，它根据以下几个条件计算奖励：

1. `optimization_improvement` 表示优化指标的改善程度，如果当前面积 `area` 小于先前记录的面积 `self.area`，则为1，如果相等则为0，否则为-1。

2. `constraint_met` 表示是否满足了约束条件，即电路的时延是否小于等于规定的时钟周期 `self.params["mapping"]["clock_period"]`。

3. `constraint_improvement` 表示约束指标的改善程度。如果约束满足且当前时延 `delay` 小于先前记录的时延 `self.delay`，则为1，如果相等则为0，否则为-1。

最后，调用 `_reward_table` 方法根据上述条件来获取奖励值。

奖励表 `_reward_table` 是一个嵌套的字典，根据约束是否满足、约束指标改善程度和优化指标改善程度来返回相应的奖励值。这里设置了一些预定义的奖励值，可以根据具体问题进行调整。

这样，通过这两个方法，就可以计算出在当前状态下执行某个操作所获得的奖励值。

## reward_table

1. `constraint_met` 表示是否满足了约束条件，即电路的时延是否小于等于规定的时钟周期。

2. `constraint_improvement` 表示约束指标的改善程度，即当前时延是否比之前的时延更小。

3. `optimization_improvement` 表示优化指标的改善程度，即当前面积是否比之前的面积更小。


`_reward_table` 是一个奖励表，它定义了在不同的情况下应该分配的奖励值。在强化学习中，奖励表用于指导智能体学习正确的行为。这里，`_reward_table` 根据三个条件的组合来分配奖励：

1. `constraint_met` 表示是否满足了约束条件，即电路的时延是否小于等于规定的时钟周期。
2. `constraint_improvement` 表示约束指标的改善程度，即当前时延是否比之前的时延更小。
3. `optimization_improvement` 表示优化指标的改善程度，即当前面积是否比之前的面积更小。

reward:

- `True` 表示约束满足，`False` 表示约束不满足。
- `constraint_improvement` 和 `optimization_improvement` 可能的取值为 `1`（改善）、`0`（相等）和 `-1`（恶化）。

具体奖励值的分配如下：

- 如果约束满足 (`constraint_met` 为 `True`)，则奖励值来自最外层字典中 `True` 对应的值。
  - 如果 `时延` 没有改善 (`contraint_improvement` 为 `0`)，则奖励值来自第二层字典中 `0` 对应的值。
    - 如果 `面积` 有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `3`。
    - 如果 `面积` 没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `0`。
    - 如果 `面积` 变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `-1`。
- 如果约束不满足 (`constraint_met` 为 `False`)，则奖励值来自最外层字典中 `False` 对应的值。
  - 如果 `时延` 有改善 (`contraint_improvement` 为 `1`)，则奖励值来自第二层字典中 `1` 对应的值。
    - 如果`面积`有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `3`。
    - 如果`面积`没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `2`。
    - 如果`面积`变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `1`。
  - 如果 `时延` 没有改善 (`contraint_improvement` 为 `0`)，则奖励值来自第二层字典中 `0` 对应的值。
    - 如果`面积`有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `2`。
    - 如果`面积`没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `0`。
    - 如果`面积`变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `-2`。
  - 如果 `时延` 变差 (`contraint_improvement` 为 `-1`)，则奖励值来自第二层字典中 `-1` 对应的值。
    - 如果`面积`有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `-1`。
    - 如果`面积`没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `-2`。
    - 如果`面积`变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `-3`。

# fpga_session

这是一个使用ABC工具进行逻辑综合优化会话的Python类。下面是对代码的简要中文解释：

1. **初始化方法 `__init__`:**
   - 初始化类实例时，将传递的参数保存在 `self.params` 中，包括优化动作和观察空间的大小等信息。
   - 设置一些初始变量，如迭代次数、剧集数、命令序列和LUT-6、Levels的初始值。
   - 初始化记录最佳指标的变量，包括最佳LUT-6、Levels，以及满足约束的最佳LUT-6。
2. **重置方法 `reset`:**
   - 在每个剧集开始时调用，用于重置环境状态。
   - 增加剧集计数，创建剧集目录，并打开用于记录日志的文件。
   - 调用 `_run` 方法执行ABC，获取状态和奖励，并将相关信息记录到日志文件中。
3. **步进方法 `step`:**
   - 接受一个优化索引作为输入，执行相应的优化，并获取新的状态和奖励。
   - 记录最佳已知的LUT-6、Levels等信息，并将这些信息写入日志文件。
4. **运行方法 `_run`:**
   - 构建ABC命令字符串，包括读取设计文件、应用优化、写入输出文件等步骤。
   - 使用 `subprocess.check_output` 执行ABC命令，获取ABC的输出，提取LUT-6和Levels，计算奖励，并获取新状态。
5. **奖励计算方法 `_get_reward`:**
   - 根据LUT-6和Levels的变化计算奖励，考虑了优化参数和约束参数的不同情况。
   - 这个方法接受两个参数 `lut_6` 和 `levels`，表示当前迭代中计算得到的LUT-6和Levels。
   - 首先，通过比较当前的LUT-6值和上一次记录的LUT-6值 `self.lut_6`，判断优化是否有改善。`optimization_improvement` 的值会被设置为：
     - `1` 表示当前的LUT-6值比上一次更好。
     - `0` 表示没有改善。
     - `-1` 表示当前的LUT-6值比上一次更差。
   - 然后，通过比较当前的Levels值和设定的FPGA映射约束值，判断约束条件是否满足。如果不满足，将 `constraint_met` 设置为 `False`。在这种情况下，会计算 `constraint_improvement` 的值，表示Levels的改善情况。
   - 最后，调用 `_reward_table` 方法，根据这些条件的组合，计算并返回最终的奖励值。
6. **奖励表 `_reward_table`:**
   - 这个方法根据 `constraint_met`（约束是否满足）、`contraint_improvement`（Levels的改善情况）、和 `optimization_improvement`（优化的改善情况）的不同组合，返回相应的奖励值。
   - 返回的奖励值存储在一个嵌套的字典结构中，根据 `constraint_met`、`contraint_improvement` 和 `optimization_improvement` 的值进行索引。
   - 奖励值表示对于给定条件的不同改善情况，系统应该给予的奖励。
7. **状态获取方法 `_get_state`:**
   - 调用 `extract_features` 函数，使用Yosys和ABC工具获取设计文件的特征，作为环境的状态。

## reward_table

这个奖励表是一个嵌套的字典，其结构如下：

- 最外层的键是 `constraint_met`，表示约束是否满足，对应的值为一个字典。
- 第二层的键是 `contraint_improvement`，表示Levels的改善情况，对应的值为一个字典。
- 第三层的键是 `optimization_improvement`，表示优化的改善情况，对应的值为奖励值。

具体奖励值的分配如下：

- 如果约束满足 (`constraint_met` 为 `True`)，则奖励值来自最外层字典中 `True` 对应的值。
  - 如果 Levels 没有改善 (`contraint_improvement` 为 `0`)，则奖励值来自第二层字典中 `0` 对应的值。
    - 如果优化有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `3`。
    - 如果优化没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `0`。
    - 如果优化变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `-1`。
- 如果约束不满足 (`constraint_met` 为 `False`)，则奖励值来自最外层字典中 `False` 对应的值。
  - 如果 Levels 有改善 (`contraint_improvement` 为 `1`)，则奖励值来自第二层字典中 `1` 对应的值。
    - 如果优化有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `3`。
    - 如果优化没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `2`。
    - 如果优化变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `1`。
  - 如果 Levels 没有改善 (`contraint_improvement` 为 `0`)，则奖励值来自第二层字典中 `0` 对应的值。
    - 如果优化有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `2`。
    - 如果优化没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `0`。
    - 如果优化变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `-2`。
  - 如果 Levels 变差 (`contraint_improvement` 为 `-1`)，则奖励值来自第二层字典中 `-1` 对应的值。
    - 如果优化有改善 (`optimization_improvement` 为 `1`)，则奖励值为 `-1`。
    - 如果优化没有改善 (`optimization_improvement` 为 `0`)，则奖励值为 `-2`。
    - 如果优化变差 (`optimization_improvement` 为 `-1`)，则奖励值为 `-3`。

这个奖励表的设计是为了根据约束是否满足、Levels和优化的改善情况，提供不同的奖励值，以引导强化学习代理的训练。

## 额外知识

在数字电路设计中，LUT-6（Look-Up Table with 6 inputs）和Levels是与逻辑综合相关的两个重要概念。

1. **LUT-6：**
   - LUT（Look-Up Table）是一种数字电路元素，它可以存储和执行任意的布尔逻辑函数。LUT-6表示这个查找表具有6个输入。
   - 在FPGA（Field-Programmable Gate Array）中，LUT-6通常用于实现更复杂的布尔逻辑功能。LUT的输入对应于电路中的信号，输出对应于逻辑函数的计算结果。

2. **Levels：**
   - 在逻辑综合中，"Levels"通常指的是电路的深度或延迟。电路的深度是指电路中的逻辑门的级别数，级别数越多，电路的延迟通常越大。
   - 逻辑综合的目标之一是优化电路，使其在满足一定约束条件的前提下，具有较小的深度和延迟，从而提高电路的性能。

在给定的代码中，LUT-6和Levels是通过ABC工具执行逻辑综合后从统计信息中提取得到的。这两个指标可以用于评估电路的性能和优化程度，以及是否满足特定的约束条件。在代码中，根据这些指标的变化，计算了相应的奖励，用于强化学习代理的训练。

# params.yml

这是一个配置文件的示例，用于配置一个逻辑综合优化环境，其中使用了 ABC 工具和 Yosys 工具。以下是配置文件中的一些关键参数的解释：

1. **`abc_binary` 和 `yosys_binary`：**
   - `abc_binary` 是 ABC 工具的二进制文件路径。
   - `yosys_binary` 是 Yosys 工具的二进制文件路径。

2. **`design_file`：**
   - `design_file` 是要进行逻辑综合的设计文件的路径，该文件必须是 ABC 工具接受的格式之一。

3. **`mapping`：**
   - `clock_period` 指定时钟周期，单位为皮秒（pico seconds）。
   - `library_file` 是标准单元库的文件路径。

4. **`fpga_mapping`：**
   - `levels` 指定 FPGA 映射的级别数。
   - `lut_inputs` 指定 FPGA 映射中 LUT 的输入数。

5. **`optimizations`：**
   - `optimizations` 是一个列表，包含要应用于逻辑综合的不同优化命令。在这个例子中，包括了一些 ABC 工具中的优化命令，例如 rewrite、refactor、resub 和 balance。

6. **`playground_dir`：**
   - `playground_dir` 是一个目录，用于存储代理（可能是一个强化学习代理）用于训练和优化的工作区。

7. **`episodes` 和 `iterations`：**
   - `episodes` 指定代理执行的总场次数。
   - `iterations` 指定每场次内执行的总迭代次数。

8. **`model_dir`：**
   - `model_dir` 是用于存储代理模型的目录路径。这是强化学习中保存训练模型的位置。

这个配置文件的目的是定义逻辑综合的环境和参数，包括使用的工具、设计文件、优化命令、工作区等。这种配置文件常用于配置和控制逻辑综合的实验或优化任务。



# Gym environment

```python
self.best_known_area = (float('inf'), float('inf'), -1, -1)
```

这段代码初始化了三个元组，每个元组包含四个浮点数。这些元组的目的是在优化问题中跟踪最佳的面积、延迟和面积满足约束条件的结果。这些元组的结构是 `(value1, value2, index1, index2)`，其中：

- `value1` 表示最佳结果的某个度量（例如，面积、延迟等）的初始值，通常设置为正无穷（`float('inf')`）。
- `value2` 表示另一个度量的初始值，同样设置为正无穷。
- `index1` 表示达到最佳结果时的某个参数或配置的索引，通常初始化为 -1。
- `index2` 是另一个参数或配置的索引，同样初始化为 -1。

这种初始化表明这些值将在程序执行过程中根据实际的优化结果而更新。在开始时，这些元组的值被设置为正无穷，以确保第一个找到的解一定比这些初始值更好。在优化过程中，如果找到了更好的解，这些元组的值将被相应地更新。

## Action apace

```
		 opt 选择执行简单的优化
     opt_clean 删除未使用的电池和电线
     opt_demorgan 使用 DeMorgan 等价物优化减少
     opt_dff 执行 DFF 优化
     opt_expr 执行 const 折叠和简单表达式重写
     opt_ffinv 通过 FF 推动逆变器
     opt_lut 优化 LUT 单元
     opt_lut_ins 丢弃未使用的 LUT 输入
     opt_mem 优化内存
     opt_mem_feedback 将内存读写端口反馈路径转换为写入使能
     opt_mem_priority 删除永远不会冲突的写入端口之间的优先级关系
     opt_mem_widen 优化所有端口都很宽的内存
     opt_merge 合并相同的单元格
     opt_muxtree 消除多路复用器树中的死树
     opt_reduce 简化大型 MUX 和 AND/OR 门
     opt_share 合并共享输入信号的相同类型的互斥单元
```



```shell
opt -fine # rewrite
opt -fine full
opt_share -full # 在 refactor 的基础上，进行零等价的重构。 

```

