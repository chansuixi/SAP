const fs = require("fs");
const path = require("path");
const InputDataDecoder = require('ethereum-input-data-decoder');
const https = require("https")
const contractAddress = "xxxxx";
const apiKey = "xxxxxx"
const etherscanApiUrl = `https://api.etherscan.io/api?module=contract&action=getsourcecode&address=${contractAddress}&apiKey=${apiKey}`;
const {execSync} = require('child_process')
const pythonScriptPath = "FuzzingwithState/code/crawl/CrawlContractGraphByFunctionName.py"
const pythonFunction = "generate_graph"
const tempFilePath = 'FuzzingwithState/code/crawl/samples/testfor/temp.txt'
const graphFilePath = 'FuzzingwithState/code/crawl/samples/testfor/graph_temp.txt'
let dir_path = "FuzzingwithState/trcode_with_input/" // metadata crawled from internet
let output_dir = "./samples/testforconstant/"
let files = fs.readdirSync(dir_path)
let fail_cnt = 0
let success_cnt = 0
let res = []
let rescnt = 0

for(let cnt = 0; cnt < files.length; cnt++) {
    try{
        console.log(cnt + '***' + files[cnt])
        let content = fs.readFileSync(dir_path+files[cnt]).toString()
        content = JSON.parse(content)
        if(content["abi"] === "Contract source code not verified" || content["abi"] === "Max rate limit reached, please use API Key for higher rate limit") {
            fail_cnt++
            continue
        }
        let abi = JSON.parse(content["abi"])
        let input = content["input"]
        if(input === "0x") {
            fail_cnt++
            continue
        }
        fs.writeFileSync(tempFilePath, content["sourceCode"])

        const decoder = new InputDataDecoder(abi)
        const result = decoder.decodeData(input)
        let methodName = result["method"]
        let methodType = result["types"]
        let paramName = result["names"]
        let inputs = []
        for(let i = 0; i < result["inputs"].length; i++) {
            if(result["types"][i].indexOf("bytes") != -1 || result["types"][i].indexOf("string") != -1){
                inputs.push(result["inputs"][i])
            } else {
                inputs.push(result["inputs"][i].toString())
            }
        }

        for(let i = 0; i < abi.length; i++) {

            if(abi[i]["name"] === methodName) {
                let functionName = methodName;

                const command = `python3 ${pythonScriptPath} "${tempFilePath}" "${functionName}"`;
                const stdout = execSync(command)
                const outputLines = stdout.toString().split('\n');
                const filteredArray = outputLines.filter(str => str.includes("Result"));
                const graph = filteredArray[0].split(': ')[1];
                const param = filteredArray[1].split(': ')[1]
                res.push({"function":abi[i], "input": inputs, "graph":graph, "param": param});
                break

            }
        }




        success_cnt++
    }catch(e){
        fail_cnt++
        console.log(e)
    }
}

console.log(res.length)
res = JSON.stringify(res)
let opts = {
    encoding: 'utf8',
    stdio: [process.stdin, process.stdout, process.stderr]
}
console.log(fail_cnt)
console.log(success_cnt)
fs.writeFileSync(output_dir + "all_funcs_need1.json", res, opts)
