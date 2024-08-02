import json
import os
import re
import time
import numpy as np
import sys
# map user-defined variables to symbolic names(var)
var_list = ['balances[msg.sender]', 'participated[msg.sender]', 'playerPendingWithdrawals[msg.sender]',
            'nonces[msgSender]', 'balances[beneficiary]', 'transactions[transactionId]', 'tokens[token][msg.sender]',
            'totalDeposited[token]', 'tokens[0][msg.sender]', 'accountBalances[msg.sender]', 'accountBalances[_to]',
            'creditedPoints[msg.sender]', 'balances[from]', 'withdrawalCount[from]', 'balances[recipient]',
            'investors[_to]', 'Bal[msg.sender]', 'Accounts[msg.sender]', 'Holders[_addr]', 'balances[_pd]',
            'ExtractDepositTime[msg.sender]', 'Bids[msg.sender]', 'participated[msg.sender]', 'deposited[_participant]',
            'Transactions[TransHash]', 'm_txs[_h]', 'balances[investor]', 'this.balance', 'proposals[_proposalID]',
            'accountBalances[accountAddress]', 'Chargers[id]', 'latestSeriesForUser[msg.sender]',
            'balanceOf[_addressToRefund]', 'tokenManage[token_]', 'milestones[_idMilestone]', 'payments[msg.sender]',
            'rewardsForA[recipient]', 'userBalance[msg.sender]', 'credit[msg.sender]', 'credit[to]', 'round_[_rd]',
            'userPendingWithdrawals[msg.sender]', '[msg.sender]', '[from]', '[to]', '[_to]', "msg.sender"]

# function limit type
function_limit = ['private', 'onlyOwner', 'internal', 'onlyGovernor', 'onlyCommittee', 'onlyAdmin', 'onlyPlayers',
                  'onlyManager', 'onlyHuman', 'only_owner', 'onlyCongressMembers', 'preventReentry', 'onlyMembers',
                  'onlyProxyOwner', 'ownerExists', 'noReentrancy', 'notExecuted', 'noReentrancy', 'noEther',
                  'notConfirmed']

# Boolean condition expression:
var_op_bool = ['!', '~', '**', '*', '!=', '<', '>', '<=', '>=', '==', '<<', '>>', '||', '&&']

# Assignment expressions
var_op_assign = ['|=', '=', '^=', '&=', '<<=', '>>=', '+=', '-=', '*=', '/=', '%=', '++', '--']


def crawl_contract_param(function : str):
    param_list = []
    f = open(function, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    for line in lines:
        text = line.strip()
        if 'public' in text or 'internal' in text or 'private' in text or 'external' in text:
            if 'function' not in text and 'constructor' not in text:
                param_list.append(text.split(' ')[-1])
    return param_list
# search all variables
def extract_variable_names(function : str):
    param_with_type_list = []
    param_list = []
    f = open(function, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    for line in lines:
        text = line.strip()
        if any(visibility in text for visibility in ['public', 'internal', 'private', 'external']):
            if 'function' not in text and 'constructor' not in text:
                
                words = [word for word in text.split() if word]
            
                if len(words) >= 2:
                    variable_name = words[-1].rstrip(';')
                    if 'mapping' in words[0]:
                       
                        variable_type_with_name = 'mapping' + '\t' + words[-1].rstrip(';')
                    else:
                        variable_type_with_name = words[0] + '\t' + words[-1].rstrip(';')
                   
                    param_list.append(variable_name)
                    param_with_type_list.append(variable_type_with_name)
    return param_list, param_with_type_list

def split_function(function:str):
    function_list = []
    f = open(function, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    flag = -1
    flag1 = 0

    for line in lines:
        text = line.strip()
        if len(text) > 0 and text != "\n":
            if text.split()[0] == "function" and len(function_list) > 0:
                flag1 = 0
        if flag1 == 0:
            if len(text) > 0 and text != "\n":
                if text.split()[0] == "function" or text.split()[0] == "function()":
                    function_list.append([text])
                    flag += 1
                elif len(function_list) > 0 and ("function" in function_list[flag][0]):
                    if text.split()[0] != "modifier" and text.split()[0] != "event":
                        function_list[flag].append(text)
                    else:
                        flag1 += 1
                        continue
        else:
            continue

    return function_list
def generate_graph(source_code_path:str , function_name : str):
    # filepath:str, function_name:str
    filepath = source_code_path
    param_list, param_with_type_list = extract_variable_names(filepath)
    allFunctionList = split_function(filepath)# Store all functions
    flag = False
    for func in allFunctionList:
        if function_name + "(" in func[0] and len(func) > 1:
            allFunctionList.clear()
            allFunctionList.append(func)
            flag = True
            break
        else:
            continue
    if flag == False:
        allFunctionList.clear()
    callValueList = []  # Store all W functions that call call.value
    cFunctionList = []  # Store a single C function that calls a W function
    CFunctionLists = []  # Store all C functions that call W function
    withdrawNameList = []  # Store the W function name that calls call.value
    otherFunctionList = []  # Store functions other than W functions
    node_list = []  # Store all the points
    edge_list = []  # Store edge and edge nips_features
    node_feature_list = []  # Store nodes feature
    params = []  # Store the parameters of the W functions
    param = []
    key_count = 0  # Number of core nodes S and W
    c_count = 0  # Number of core nodes C

    # ======================================================================
    # ---------------------------  Handle nodes  ----------------------------
    # ======================================================================

    # Store functions other than W functions
    for i in range(len(allFunctionList)):
        flag = 0
        for j in range(len(allFunctionList[i])):
            text = allFunctionList[i][j]
            if '.call.value' in text:
                flag += 1
        if flag == 0:
            otherFunctionList.append(allFunctionList[i])

    # Traverse all functions, find the call.value keyword, store the S and W nodes
    for i in range(len(allFunctionList)):
        for j in range(len(allFunctionList[i])):
            text = allFunctionList[i][j]
            if '.call.value' in text:
                node_list.append("S")
                node_list.append("W" + str(key_count))
                callValueList.append([allFunctionList[i], "S", "W" + str(key_count)])

                # get the function name and params
                ss = allFunctionList[i][0]
                pp = re.compile(r'[(](.*?)[)]', re.S)
                result = re.findall(pp, ss)
                result_params = result[0].split(",")

                for n in range(len(result_params)):
                    param.append(result_params[n].strip().split(" ")[-1])

                params.append([param, "S", "W" + str(key_count)])

                # Handling W function access restrictions, which can be used for access restriction properties
                # default that there are C nodes
                limit_count = 0
                for k in range(len(function_limit)):
                    if function_limit[k] in callValueList[key_count][0][0]:
                        limit_count += 1
                        if "address" in text:
                            node_feature_list.append(
                                ["S", "S", "LimitedAC", ["W" + str(key_count)],
                                 2, "INNADD"])
                            node_feature_list.append(
                                ["W" + str(key_count), "W" + str(key_count), "LimitedAC", [],
                                 1, "NULL"])
                            break
                        elif "msg.sender" in text:
                            node_feature_list.append(
                                ["S", "S", "LimitedAC", ["W" + str(key_count)],
                                 2, "MSG"])
                            node_feature_list.append(
                                ["W" + str(key_count), "W" + str(key_count), "LimitedAC", [],
                                 1, "NULL"])
                            break
                        else:
                            param_count = 0
                            for pa in param:
                                if pa in text and pa != "":
                                    param_count += 1
                                    node_feature_list.append(
                                        ["S", "S", "LimitedAC",
                                         ["W" + str(key_count)],
                                         2, "MSG"])
                                    node_feature_list.append(
                                        ["W" + str(key_count), "W" + str(key_count), "LimitedAC", [],
                                         1, "NULL"])
                                    break
                            if param_count == 0:
                                node_feature_list.append(
                                    ["S", "S", "LimitedAC", ["W" + str(key_count)],
                                     2, "INNADD"])
                                node_feature_list.append(
                                    ["W" + str(key_count), "W" + str(key_count), "LimitedAC", [],
                                     1, "NULL"])
                            break
                if limit_count == 0:
                    if "address" in text:
                        node_feature_list.append(
                            ["S", "S", "NoLimit", ["W" + str(key_count)],
                             2, "INNADD"])
                        node_feature_list.append(
                            ["W" + str(key_count), "W" + str(key_count), "NoLimit", [],
                             1, "NULL"])
                    elif "msg.sender" in text:
                        node_feature_list.append(
                            ["S", "S", "NoLimit", ["W" + str(key_count)],
                             2, "MSG"])
                        node_feature_list.append(
                            ["W" + str(key_count), "W" + str(key_count), "NoLimit", [],
                             1, "NULL"])
                    else:
                        param_count = 0
                        for pa in param:
                            if pa in text and pa != "":
                                param_count += 1
                                node_feature_list.append(
                                    ["S", "S", "NoLimit", ["W" + str(key_count)],
                                     2, "MSG"])
                                node_feature_list.append(
                                    ["W" + str(key_count), "W" + str(key_count), "NoLimit", [],
                                     1, "NULL"])
                                break
                        if param_count == 0:
                            node_feature_list.append(
                                ["S", "S", "NoLimit", ["W" + str(key_count)],
                                 2, "INNADD"])
                            node_feature_list.append(
                                ["W" + str(key_count), "W" + str(key_count), "NoLimit", [],
                                 1, "NULL"])

                # For example: function transfer(address _to, uint _value, bytes _data, string _custom_fallback)
                # get function name (transfer)
                tmp = re.compile(r'\b([_A-Za-z]\w*)\b(?:(?=\s*\w+\()|(?!\s*\w+))')
                result_withdraw = tmp.findall(allFunctionList[i][0])
                withdrawNameTmp = result_withdraw[1]
                if withdrawNameTmp == "payable":
                    withdrawName = withdrawNameTmp
                else:
                    withdrawName = withdrawNameTmp + "("
                withdrawNameList.append(["W" + str(key_count), withdrawName])

                key_count += 1

    if key_count == 0:
        # print("Currently, there is no key word call.value")
        node_feature_list.append(["S", "S", "NoLimit", ["NULL"], 0, "NULL"])
        node_feature_list.append(["W0", "W0", "NoLimit", ["NULL"], 0, "NULL"])
        node_feature_list.append(["C0", "C0", "NoLimit", ["NULL"], 0, "NULL"])
    else:
        # Traverse all functions and find the C function nodes that calls the W function
        # (determine the function call by matching the number of arguments)
        for k in range(len(withdrawNameList)):
            w_key = withdrawNameList[k][0]
            w_name = withdrawNameList[k][1]
            for i in range(len(otherFunctionList)):
                if len(otherFunctionList[i]) > 2:
                    for j in range(1, len(otherFunctionList[i])):
                        text = otherFunctionList[i][j]
                        if w_name in text:
                            p = re.compile(r'[(](.*?)[)]', re.S)
                            result = re.findall(p, text)
                            result_params = result[0].split(",")

                            if result_params[0] != "" and len(result_params) == len(params[k][0]):
                                cFunctionList += otherFunctionList[i]
                                CFunctionLists.append(
                                    [w_key, w_name, "C" + str(c_count), otherFunctionList[i]])
                                node_list.append("C" + str(c_count))

                                for n in range(len(node_feature_list)):
                                    if w_key in node_feature_list[n][0]:
                                        node_feature_list[n][3].append("C" + str(c_count))

                                # Handling C function access restrictions
                                limit_count = 0
                                for m in range(len(function_limit)):
                                    if function_limit[m] in cFunctionList[0]:
                                        limit_count += 1
                                        node_feature_list.append(
                                            ["C" + str(c_count), "C" + str(c_count), "LimitedAC", ["NULL"], 0, "NULL"])
                                        break
                                if limit_count == 0:
                                    node_feature_list.append(
                                        ["C" + str(c_count), "C" + str(c_count), "NoLimit", ["NULL"], 0, "NULL"])
                                c_count += 1
                                break

        if c_count == 0:
            print("There is no C node")
            node_list.append("C0")
            node_feature_list.append(["C0", "C0", "NoLimit", ["NULL"], 0, "NULL"])
            for n in range(len(node_feature_list)):
                if "W" in node_feature_list[n][0]:
                    node_feature_list[n][3] = ["NULL"]

        # ======================================================================
        # ---------------------------  Handle edge  ----------------------------
        # ======================================================================

        # (1) W->S (include: W->VAR, VAR->S, S->VAR)
        for i in range(len(callValueList)):
            flag = 0  # flag: flag = 0, before call.value; flag > 0, after call.value
            before_var_count = 0
            after_var_count = 0
            var_tmp = []
            var_name = []
            var_w_name = []
            for j in range(len(callValueList[i][0])):
                text = callValueList[i][0][j]
                if '.call.value' not in text:
                    if flag == 0:
                        # print("before call.value")
                        # handle W -> VAR
                        for k in range(len(var_list)):
                            if var_list[k] in text:
                                node_list.append("VAR" + str(before_var_count))
                                var_tmp.append("VAR" + str(before_var_count))

                                if len(var_w_name) == 0:
                                    if "assert" in text:
                                        edge_list.append(
                                            [callValueList[i][2], "VAR" + str(before_var_count), callValueList[i][2], 1,
                                             'AH'])
                                    elif "require" in text:
                                        edge_list.append(
                                            [callValueList[i][2], "VAR" + str(before_var_count), callValueList[i][2], 1,
                                             'RG'])
                                    elif j >= 1:
                                        if "if" in callValueList[i][0][j - 1]:
                                            edge_list.append(
                                                [callValueList[i][2], "VAR" + str(before_var_count),
                                                 callValueList[i][2], 1,
                                                 'GN'])
                                        elif "for" in callValueList[i][0][j - 1]:
                                            edge_list.append(
                                                [callValueList[i][2], "VAR" + str(before_var_count),
                                                 callValueList[i][2], 1,
                                                 'FOR'])
                                        elif "else" in callValueList[i][0][j - 1]:
                                            edge_list.append(
                                                [callValueList[i][2], "VAR" + str(before_var_count),
                                                 callValueList[i][2], 1,
                                                 'GB'])
                                        elif j + 1 < len(callValueList[i][0]):
                                            if "if" and "throw" in callValueList[i][0][j] or "if" in \
                                                    callValueList[i][0][j] \
                                                    and "throw" in callValueList[i][0][j + 1]:
                                                edge_list.append(
                                                    [callValueList[i][2], "VAR" + str(before_var_count),
                                                     callValueList[i][2], 1, 'IT'])
                                            elif "if" and "revert" in callValueList[i][0][j] or "if" in \
                                                    callValueList[i][0][
                                                        j] and "revert" in callValueList[i][0][j + 1]:
                                                edge_list.append(
                                                    [callValueList[i][2], "VAR" + str(before_var_count),
                                                     callValueList[i][2], 1, 'RH'])
                                            elif "if" in text:
                                                edge_list.append(
                                                    [callValueList[i][2], "VAR" + str(before_var_count),
                                                     callValueList[i][2], 1, 'IF'])
                                            else:
                                                edge_list.append(
                                                    [callValueList[i][2], "VAR" + str(before_var_count),
                                                     callValueList[i][2], 1, 'FW'])
                                        else:
                                            edge_list.append(
                                                [callValueList[i][2], "VAR" + str(before_var_count),
                                                 callValueList[i][2], 1,
                                                 'FW'])
                                    else:
                                        edge_list.append(
                                            [callValueList[i][2], "VAR" + str(before_var_count), callValueList[i][2], 1,
                                             'FW'])

                                    var_node = 0
                                    var_bool_node = 0
                                    for b in range(len(var_op_bool)):
                                        if var_op_bool[b] in text:
                                            node_feature_list.append(
                                                ["VAR" + str(before_var_count), "VAR" + str(before_var_count),
                                                 callValueList[i][2], 1, 'BOOL'])
                                            var_node += 1
                                            var_bool_node += 1
                                            break

                                    if var_bool_node == 0:
                                        for a in range(len(var_op_assign)):
                                            if var_op_assign[a] in text:
                                                node_feature_list.append(
                                                    ["VAR" + str(before_var_count), "VAR" + str(before_var_count),
                                                     callValueList[i][2], 1, 'ASSIGN'])
                                                var_node += 1
                                                break

                                    if var_node == 0:
                                        node_feature_list.append(
                                            ["VAR" + str(before_var_count), "VAR" + str(before_var_count),
                                             callValueList[i][2], 1, 'NULL'])

                                    var_w_name.append(var_list[k])
                                    var_name.append(var_list[k])
                                    before_var_count += 1
                                else:
                                    var_w_count = 0
                                    for n in range(len(var_w_name)):
                                        if var_list[k] == var_w_name[n]:
                                            var_w_count += 1
                                            var_tmp.append(var_tmp[len(var_tmp) - 1])

                                            var_node = 0
                                            var_bool_node = 0
                                            for b in range(len(var_op_bool)):
                                                if var_op_bool[b] in text:
                                                    node_feature_list.append(
                                                        [var_tmp[len(var_tmp) - 1], var_tmp[len(var_tmp) - 1],
                                                         callValueList[i][2], 1, 'BOOL'])
                                                    var_bool_node += 1
                                                    var_node += 1
                                                    break

                                            if var_bool_node == 0:
                                                for a in range(len(var_op_assign)):
                                                    if var_op_assign[a] in text:
                                                        node_feature_list.append(
                                                            [var_tmp[len(var_tmp) - 1], var_tmp[len(var_tmp) - 1],
                                                             callValueList[i][2], 1, 'ASSIGN'])
                                                        var_node += 1
                                                        break

                                            if var_node == 0:
                                                node_feature_list.append(
                                                    [var_tmp[len(var_tmp) - 1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][2], 1, 'NULL'])

                                    if var_w_count == 0:
                                        var_node = 0
                                        var_bool_node = 0
                                        var_tmp.append("VAR" + str(before_var_count))

                                        for b in range(len(var_op_bool)):
                                            if var_op_bool[b] in text:
                                                node_feature_list.append(
                                                    ["VAR" + str(before_var_count), "VAR" + str(before_var_count),
                                                     callValueList[i][2], 1, 'BOOL'])
                                                var_node += 1
                                                var_bool_node += 1
                                                break

                                        if var_bool_node == 0:
                                            for a in range(len(var_op_assign)):
                                                if var_op_assign[a] in text:
                                                    node_feature_list.append(
                                                        ["VAR" + str(before_var_count), "VAR" + str(before_var_count),
                                                         callValueList[i][2], 1, 'ASSIGN'])
                                                    var_node += 1
                                                    break

                                        if var_node == 0:
                                            node_feature_list.append(
                                                ["VAR" + str(before_var_count), "VAR" + str(before_var_count),
                                                 callValueList[i][2], 1, 'NULL'])

                    elif flag != 0:
                        # print("after call.value")
                        # handle S->VAR
                        var_count = 0
                        for k in range(len(var_list)):
                            if var_list[k] in text:
                                if before_var_count == 0:
                                    node_list.append("VAR" + str(after_var_count))
                                    var_tmp.append("VAR" + str(after_var_count))

                                    if "assert" in text:
                                        edge_list.append(
                                            [callValueList[i][1], "VAR" + str(after_var_count), callValueList[i][1], 3,
                                             'AH'])
                                    elif "require" in text:
                                        edge_list.append(
                                            [callValueList[i][1], "VAR" + str(after_var_count), callValueList[i][1], 3,
                                             'RG'])
                                    elif "return" in text:
                                        edge_list.append(
                                            [callValueList[i][1], "VAR" + str(after_var_count), callValueList[i][1], 3,
                                             'RE'])
                                    elif "if" and "throw" in text:
                                        edge_list.append(
                                            [callValueList[i][1], "VAR" + str(after_var_count), callValueList[i][1], 3,
                                             'IT'])
                                    elif "if" and "revert" in text:
                                        edge_list.append(
                                            [callValueList[i][1], "VAR" + str(after_var_count), callValueList[i][1], 3,
                                             'RH'])
                                    elif "if" in text:
                                        edge_list.append(
                                            [callValueList[i][1], "VAR" + str(after_var_count), callValueList[i][1], 3,
                                             'IF'])
                                    else:
                                        edge_list.append(
                                            [callValueList[i][1], "VAR" + str(after_var_count), callValueList[i][1], 3,
                                             'FW'])

                                    var_node = 0
                                    var_bool_node = 0
                                    for b in range(len(var_op_bool)):
                                        if var_op_bool[b] in text:
                                            node_feature_list.append(
                                                ["VAR" + str(after_var_count), "VAR" + str(after_var_count),
                                                 callValueList[i][1], 3, 'BOOL'])
                                            var_node += 1
                                            var_bool_node += 1
                                            break

                                    if var_bool_node == 0:
                                        for a in range(len(var_op_assign)):
                                            if var_op_assign[a] in text:
                                                node_feature_list.append(
                                                    ["VAR" + str(after_var_count), "VAR" + str(after_var_count),
                                                     callValueList[i][1], 3, 'ASSIGN'])
                                                var_node += 1
                                                break

                                    if var_node == 0:
                                        node_feature_list.append(
                                            ["VAR" + str(after_var_count), "VAR" + str(after_var_count),
                                             callValueList[i][1], 3, 'NULL'])

                                    # after_var_count += 1

                                elif before_var_count > 0:
                                    for n in range(len(var_name)):
                                        if var_list[k] == var_name[n]:
                                            var_count += 1
                                            if "assert" in text:
                                                edge_list.append(
                                                    [callValueList[i][1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][1], 3,
                                                     'AH'])
                                            elif "require" in text:
                                                edge_list.append(
                                                    [callValueList[i][1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][1], 3,
                                                     'RG'])
                                            elif "return" in text:
                                                edge_list.append(
                                                    [callValueList[i][1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][1], 3,
                                                     'RE'])
                                            elif "if" and "throw" in text:
                                                edge_list.append(
                                                    [callValueList[i][1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][1], 3,
                                                     'IT'])
                                            elif "if" and "revert" in text:
                                                edge_list.append(
                                                    [callValueList[i][1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][1], 3,
                                                     'RH'])
                                            elif "if" in text:
                                                edge_list.append(
                                                    [callValueList[i][1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][1], 3,
                                                     'IF'])
                                            else:
                                                edge_list.append(
                                                    [callValueList[i][1], var_tmp[len(var_tmp) - 1],
                                                     callValueList[i][1], 3,
                                                     'FW'])

                                            after_var_count += 1

                elif '.call.value' in text:
                    flag += 1

                    if len(var_tmp) > 0:
                        if "assert" in text:
                            edge_list.append(
                                [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'AH'])
                        elif "require" in text:
                            edge_list.append(
                                [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'RG'])
                        elif "return" in text:
                            edge_list.append(
                                [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'RE'])
                        elif j > 1:
                            if "if" in callValueList[i][0][j - 1]:
                                edge_list.append(
                                    [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'GN'])
                            elif "for" in callValueList[i][0][j - 1]:
                                edge_list.append(
                                    [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'FOR'])
                            elif "else" in callValueList[i][0][j - 1]:
                                edge_list.append(
                                    [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'GB'])
                            elif j + 1 < len(callValueList[i][0]):
                                if "if" and "throw" in callValueList[i][0][j] or "if" in callValueList[i][0][j] \
                                        and "throw" in callValueList[i][0][j + 1]:
                                    edge_list.append(
                                        [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'IT'])
                                elif "if" and "revert" in callValueList[i][0][j] or "if" in callValueList[i][0][j] \
                                        and "revert" in callValueList[i][0][j + 1]:
                                    edge_list.append(
                                        [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'RH'])
                                elif "if" in text:
                                    edge_list.append(
                                        [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'IF'])
                                else:
                                    edge_list.append(
                                        [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'FW'])
                            else:
                                edge_list.append(
                                    [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'FW'])
                        else:
                            edge_list.append(
                                [var_tmp[len(var_tmp) - 1], callValueList[i][1], callValueList[i][2], 2, 'FW'])

                    elif len(var_tmp) == 0:
                        if "assert" in text:
                            edge_list.append(
                                [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'AH'])
                        elif "require" in text:
                            edge_list.append(
                                [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'RG'])
                        elif "return" in text:
                            edge_list.append(
                                [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'RE'])
                        elif j > 1:
                            if "if" in callValueList[i][0][j - 1]:
                                edge_list.append(
                                    [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'GN'])
                            elif "for" in callValueList[i][0][j - 1]:
                                edge_list.append(
                                    [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'FOR'])
                            elif "else" in callValueList[i][0][j - 1]:
                                edge_list.append(
                                    [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'GB'])
                            elif j + 1 < len(callValueList[i][0]):
                                if "if" and "throw" in callValueList[i][0][j] or "if" in callValueList[i][0][j] \
                                        and "throw" in callValueList[i][0][j + 1]:
                                    edge_list.append(
                                        [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'IT'])
                                elif "if" and "revert" in callValueList[i][0][j] or "if" in callValueList[i][0][j] \
                                        and "revert" in callValueList[i][0][j + 1]:
                                    edge_list.append(
                                        [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'RH'])
                                elif "if" in text:
                                    edge_list.append(
                                        [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'IF'])
                                else:
                                    edge_list.append(
                                        [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'FW'])
                            else:
                                edge_list.append(
                                    [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'FW'])
                        else:
                            edge_list.append(
                                [callValueList[i][2], callValueList[i][1], callValueList[i][2], 1, 'FW'])

        # (2) handle C->W (include C->VAR, VAR->W)
        for i in range(len(CFunctionLists)):
            for j in range(len(CFunctionLists[i][3])):
                text = CFunctionLists[i][3][j]
                var_flag = 0
                for k in range(len(var_list)):
                    if var_list[k] in text:
                        var_flag += 1

                        var_node = 0
                        var_bool_node = 0
                        for b in range(len(var_op_bool)):
                            if var_op_bool[b] in text:
                                node_feature_list.append(
                                    ["VAR" + str(len(var_tmp)), "VAR" + str(len(var_tmp)),
                                     CFunctionLists[i][2], 1, 'BOOL'])
                                var_node += 1
                                var_bool_node += 1
                                break

                        if var_bool_node == 0:
                            for a in range(len(var_op_assign)):
                                if var_op_assign[a] in text:
                                    node_feature_list.append(
                                        ["VAR" + str(len(var_tmp)), "VAR" + str(len(var_tmp)),
                                         CFunctionLists[i][2], 1, 'ASSIGN'])
                                    var_node += 1
                                    break

                        if var_node == 0:
                            node_feature_list.append(
                                ["VAR" + str(len(var_tmp)), "VAR" + str(len(var_tmp)),
                                 CFunctionLists[i][2], 1, 'NULL'])

                        if "assert" in text:
                            edge_list.append(
                                [CFunctionLists[i][2], "VAR" + str(len(var_tmp)), CFunctionLists[i][2], 1, 'AH'])
                            edge_list.append(
                                ["VAR" + str(len(var_tmp)), CFunctionLists[i][0], CFunctionLists[i][2], 2, 'FW'])
                        elif "require" in text:
                            edge_list.append(
                                [CFunctionLists[i][2], "VAR" + str(len(var_tmp)), CFunctionLists[i][2], 1, 'RG'])
                            edge_list.append(
                                ["VAR" + str(len(var_tmp)), CFunctionLists[i][0], CFunctionLists[i][2], 2, 'FW'])
                        elif "if" and "throw" in text:
                            edge_list.append(
                                [CFunctionLists[i][2], "VAR" + str(len(var_tmp)), CFunctionLists[i][2], 1, 'IT'])
                            edge_list.append(
                                ["VAR" + str(len(var_tmp)), CFunctionLists[i][0], CFunctionLists[i][2], 2, 'FW'])
                        elif "if" and "revert" in text:
                            edge_list.append(
                                [CFunctionLists[i][2], "VAR" + str(len(var_tmp)), CFunctionLists[i][2], 1, 'RH'])
                            edge_list.append(
                                ["VAR" + str(len(var_tmp)), CFunctionLists[i][0], CFunctionLists[i][2], 2, 'FW'])
                        elif "if" in text:
                            edge_list.append(
                                [CFunctionLists[i][2], "VAR" + str(len(var_tmp)), CFunctionLists[i][2], 1, 'IF'])
                            edge_list.append(
                                ["VAR" + str(len(var_tmp)), CFunctionLists[i][0], CFunctionLists[i][2], 2, 'FW'])
                        else:
                            edge_list.append(
                                [CFunctionLists[i][2], "VAR" + str(len(var_tmp)), CFunctionLists[i][2], 1, 'FW'])
                            edge_list.append(
                                ["VAR" + str(len(var_tmp)), CFunctionLists[i][0], CFunctionLists[i][2], 2, 'FW'])
                        break

                if var_flag == 0:
                    if "assert" in text:
                        edge_list.append(
                            [CFunctionLists[i][2], CFunctionLists[i][0], CFunctionLists[i][2], 1, 'AH'])
                    elif "require" in text:
                        edge_list.append(
                            [CFunctionLists[i][2], CFunctionLists[i][0], CFunctionLists[i][2], 1, 'RG'])
                    elif "if" and "throw" in text:
                        edge_list.append(
                            [CFunctionLists[i][2], CFunctionLists[i][0], CFunctionLists[i][2], 1, 'IT'])
                    elif "if" and "revert" in text:
                        edge_list.append(
                            [CFunctionLists[i][2], CFunctionLists[i][0], CFunctionLists[i][2], 1, 'RH'])
                    elif "if" in text:
                        edge_list.append(
                            [CFunctionLists[i][2], CFunctionLists[i][0], CFunctionLists[i][2], 1, 'IF'])
                    else:
                        edge_list.append(
                            [CFunctionLists[i][2], CFunctionLists[i][0], CFunctionLists[i][2], 1, 'FW'])
                    break
                else:
                    print("The C function does not call the corresponding W function")

    # Handling some duplicate elements, the filter leaves a unique
    edge_list = list(set([tuple(t) for t in edge_list]))
    edge_list = [list(v) for v in edge_list]
    node_feature_list_new = []
    [node_feature_list_new.append(i) for i in node_feature_list if not i in node_feature_list_new]
    # node_feature_list = list(set([tuple(t) for t in node_feature_list]))
    # node_feature_list = [list(v) for v in node_feature_list]
    # node_list = list(set(node_list))
    used_param = []
    if len(allFunctionList) >= 1:
        for func_line in allFunctionList[0]:
            for i in range(len(param_list)):
                if param_list[i] in func_line and param_with_type_list[i] not in used_param:
                    used_param.append(param_with_type_list[i])
    res = generate_red_sig(edge_list)

    return res, used_param

def generate_red_sig(edge_list):
    sig_red = ''
    sorted_array = sorted(edge_list, key=lambda x: x[3])
    for item_list in sorted_array:
        if sig_red == '':
            sig_red = item_list[-1]
        else:
            sig_red = sig_red + "," + item_list[-1]
    return sig_red


if __name__ == '__main__':
    param1 = sys.argv[1]
    param2 = sys.argv[2]
   
    res, param_list = generate_graph(param1,param2)
    print(f"Result_1: {res}\nResult_2: {param_list}")
    