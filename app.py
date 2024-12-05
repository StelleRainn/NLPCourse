from flask import Flask, render_template, request, jsonify
import torch
from transformers import BertTokenizerFast, BertForQuestionAnswering

# 设置设备
device = "cuda" if torch.cuda.is_available() else "cpu"

# 加载模型和分词器
tokenizer = BertTokenizerFast.from_pretrained("bert-base-chinese")
model = BertForQuestionAnswering.from_pretrained("./fengchao-bert-qa").to(device)

# Flask 应用实例
app = Flask(__name__)

# 定义预测函数
def predict(doc, query):
    item = tokenizer(
        [doc, query], max_length=512, return_tensors="pt", truncation=True, padding=True
    )
    with torch.no_grad():
        input_ids = item["input_ids"].to(device).reshape(1, -1)
        attention_mask = item["attention_mask"].to(device).reshape(1, -1)
        outputs = model(input_ids[:, :512], attention_mask[:, :512])

        start_pred = torch.argmax(outputs.start_logits, dim=1)
        end_pred = torch.argmax(outputs.end_logits, dim=1)

    try:
        start_pred = item.token_to_chars(0, start_pred)
        end_pred = item.token_to_chars(0, end_pred)
    except:
        return "无法找到答案"

    if start_pred.start > end_pred.end:
        return "无法找到答案"
    else:
        return doc[start_pred.start : end_pred.end]

# 路由和逻辑
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        doc = request.form["doc"]
        query = request.form["query"]
        answer = predict(doc, query)
        return render_template("index.html", doc=doc, query=query, answer=answer)
    return render_template("index.html", doc="", query="", answer="")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
