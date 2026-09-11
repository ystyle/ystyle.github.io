'use strict';

/**
 * 修正 hexo-generator-feed 生成的 atom.xml 摘要。
 *
 * 背景：把 feed 的 content 设为 false 后，插件改用 <summary>，但它是对
 * post.content 做「定长硬截断」（content_limit 个字符），于是：
 *   1) 截断点可能落在标签中间，产生 `...<hr`、`...<h2 id="背景"` 这类残尾；
 *   2) 不会补齐未闭合标签，摘要里出现未闭合的 <ul>/<li>/<blockquote> 等。
 * 两者都会让订阅器渲染出错。这里在生成完成后对每条 summary 做两步清理：
 *   切掉残缺尾部 → 补齐未闭合标签。
 */

const fs = require('fs');
const pathFn = require('path');

const VOID_TAGS = {
  area: 1, base: 1, br: 1, col: 1, embed: 1, hr: 1, img: 1, input: 1,
  link: 1, meta: 1, param: 1, source: 1, track: 1, wbr: 1
};

function balanceHtml(html) {
  // 1) 切掉尾部残缺标签：最后一个 '<' 之后没有 '>' 的部分
  const lt = html.lastIndexOf('<');
  const gt = html.lastIndexOf('>');
  if (lt > gt) html = html.slice(0, lt);

  // 2) 用栈补齐未闭合标签
  const stack = [];
  const re = /<(\/?)([a-zA-Z][a-zA-Z0-9-]*)\b[^>]*?(\/?)>/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    const isClose = m[1] === '/';
    const tag = m[2].toLowerCase();
    const selfClose = m[3] === '/';

    if (VOID_TAGS[tag] || selfClose) continue;

    if (isClose) {
      const idx = stack.lastIndexOf(tag);
      if (idx !== -1) stack.length = idx;
    } else {
      stack.push(tag);
    }
  }

  return html + stack.reverse().map(t => '</' + t + '>').join('');
}

function decodeEntities(s) {
  // 注意顺序：先解 &lt;/&gt; 等，最后解 &amp;，避免 &amp;lt; 被二次解码
  return s
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&');
}

function encodeEntities(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// 注意：不能挂在 after_generate 上 —— 它在 hexo.load() 内部、_generate() 结束时触发，
// 而真正的写文件动作发生在更晚的 console/generate.js firstGenerate() 里，
// 那时 public/atom.xml 还没被写入。before_exit 在命令收尾时触发，文件已就绪。
hexo.extend.filter.register('before_exit', function () {
  const file = pathFn.join(hexo.public_dir, 'atom.xml');
  if (!fs.existsSync(file)) return;

  const xml = fs.readFileSync(file, 'utf8');
  let touched = 0;

  const fixed = xml.replace(
    /(<summary type="html">)([\s\S]*?)(<\/summary>)/g,
    function (all, open, inner, close) {
      const cleaned = balanceHtml(decodeEntities(inner).trim());
      const out = open + encodeEntities(cleaned) + close;
      if (out !== all) touched++;
      return out;
    }
  );

  if (fixed !== xml) {
    fs.writeFileSync(file, fixed);
    hexo.log.info('feed summary 已清理：%d 条', touched);
  }
});
