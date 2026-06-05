async function triggerCrawl() {
    var btn = document.getElementById('crawlBtn');
    if (!btn || btn.classList.contains('loading')) return;

    btn.classList.add('loading');
    btn.textContent = '⏳ 수집 중...';
    btn.disabled = true;

    fetch('/api/crawl', { method: 'POST' })
        .then(function(resp) { return resp.json(); })
        .then(function(data) {
            if (data.status === 'success') {
                showToast('✅ 수집 완료! 신규 ' + data.total_new + '건 추가', 'success');
                setTimeout(function() { location.reload(); }, 1500);
            } else {
                showToast('❌ 오류: ' + data.message, 'error');
            }
        })
        .catch(function(err) {
            showToast('❌ 서버 연결 실패', 'error');
            console.error('Crawl error:', err);
        })
        .finally(function() {
            btn.classList.remove('loading');
            btn.textContent = '🔄 지금 수집';
            btn.disabled = false;
        });
}

function showToast(message, type, duration) {
    type = type || 'success';
    duration = duration || 3000;

    var toast = document.getElementById('toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = 'toast ' + type;

    if (toast._timer) clearTimeout(toast._timer);
    toast._timer = setTimeout(function() {
        toast.className = 'toast hidden';
    }, duration);
}

document.addEventListener('DOMContentLoaded', function() {
    var bars = document.querySelectorAll('.bar-fill');
    bars.forEach(function(bar) {
        var target = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function() {
            bar.style.width = target;
        }, 100);
    });
});
