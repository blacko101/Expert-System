// static/support_app/main.js
$(function(){
  const $form = $('#diagnose-form');
  const $results = $('#results');
  const $cards = $('#result-cards');
  const $spinner = $('#spinner');

  // Example loader
  $('#example-btn').on('click', function(){
    const example = JSON.stringify({
      ping_latency: 250,
      speed_mbps: 0.4,
      wifi_connected: true,
      ping_ip: "success",
      ping_domain: "fail",
      cpu_temp: 85,
      popups: true,
      idle_cpu: 95,
      disk_health: 40,
      ram_usage: 92
    }, null, 2);
    $('#id_structured').val(example);
    alert('Example loaded into Advanced JSON field.');
  });

  $form.on('submit', function(ev){
    ev.preventDefault();
    $spinner.show();
    $cards.empty();
    $results.show();
    const data = $form.serialize();
    $.post($form.attr('action'), data, function(resp){
      $spinner.hide();
      if(resp.ok){
        const diag = resp.diagnoses;
        if(diag.length===0){
          $cards.append('<div class="result-card">No diagnosis found. Collect more data.</div>');
          return;
        }
        diag.forEach(function(d){
          const $c = $('<div class="result-card"></div>');
          $c.append(`<h3>${d.name}</h3>`);
          $c.append(`<p class="small"><strong>Confidence:</strong> ${Math.round(d.confidence*100)}%</p>`);
          $c.append(`<p><strong>Evidence:</strong> ${d.evidence}</p>`);
          $c.append(`<p><strong>Remedy:</strong> ${d.remedy}</p>`);
          $cards.append($c);
        });
        $cards.prepend(`<p class="small">Case ID: ${resp.case_id}</p>`);
      } else {
        $cards.append('<div class="result-card">Error running diagnosis.</div>');
      }
    }).fail(function(xhr){
      $spinner.hide();
      const err = xhr.responseJSON && xhr.responseJSON.errors ? JSON.stringify(xhr.responseJSON.errors) : 'Server error';
      $cards.append(`<div class="result-card">${err}</div>`);
    });
  });
});
