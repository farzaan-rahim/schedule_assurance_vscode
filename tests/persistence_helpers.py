from pathlib import Path
from tests.test_analysis_anchors import controlled_xer


def rich_xer():
    # A new proprietary-free fixture; existing source fixtures remain untouched.
    text=controlled_xer().decode().replace('%E\n','')
    def table(name,fields,rows):
        nonlocal text
        text+='%T\t'+name+'\n%F\t'+'\t'.join(fields)+'\n'
        for row in rows:text+='%R\t'+'\t'.join('' if x is None else str(x) for x in row)+'\n'
    table('RSRC',['rsrc_id','rsrc_short_name','rsrc_name','parent_rsrc_id','clndr_id','rsrc_type','active_flag'],
        [('R0','ROOT','Resource root','','','RT_Labor','Y'),('R1','LAB','Synthetic labour','R0','C1','RT_Labor','Y')])
    table('TASKRSRC',['taskrsrc_id','task_id','rsrc_id','remain_qty','target_qty','act_reg_qty','act_ot_qty','target_cost','act_reg_cost','act_ot_cost','remain_cost','cost_per_qty','target_start_date','target_end_date'],
        [('ASSIGN','0','R1','1.25','2.5','1','0.5','123.456789123','50.125','7.75','65.581789123','49.3827156492','2026-01-05 08:00','2026-01-05 10:00')])
    table('ACTVTYPE',['actv_code_type_id','actv_code_type','proj_id','wbs_id','actv_code_type_scope','seq_num'],[('T1','Discipline','P1','W1','AS_Project',1)])
    table('ACTVCODE',['actv_code_id','actv_code_type_id','parent_actv_code_id','actv_code_name','short_name','seq_num'],
        [('V0','T1','','Root discipline','ROOT',1),('V1','T1','V0','Synthetic discipline','SYN',2)])
    table('TASKACTV',['task_id','actv_code_type_id','actv_code_id','proj_id'],[('0','T1','V1','P1')])
    table('UDFTYPE',['udf_type_id','table_name','udf_type_name','udf_type_label','logical_data_type'],
        [('U1','TASK','Text','Text','FT_TEXT'),('U2','PROJECT','Project marker','Project marker','FT_TEXT'),('U3','TASK','Date','Date','FT_DATE'),('U4','TASK','Number','Number','FT_NUMBER'),('U5','TASK','Invalid number','Invalid number','FT_NUMBER')])
    # PROJECT foreign ID intentionally coincides with a TASK ID; never link it to TASK.
    table('UDFVALUE',['udf_type_id','fk_id','proj_id','udf_text','udf_number','udf_date'],
        [('U1','0','P1','Alpha','',''),('U2','0','P1','Project only','',''),('U3','1','P1','','','2026-01-05 09:00'),('U4','0','P1','','123.5',''),('U5','0','P1','','not-a-number','')])
    return (text+'%E\n').encode()



def detailed_xer():
    # Preserve populated optional imported fields, independent of schedulability.
    extra=['target_start_date','target_end_date','act_start_date','act_end_date','expect_end_date','restart_date','reend_date',
        'duration_type','suspend_date','resume_date','cstr_type','cstr_date','cstr_type2','cstr_date2','phys_complete_pct']
    values=['2026-01-01 08:00','2026-01-02 17:00','2026-01-01 09:00','2026-01-02 16:00','2026-01-07 16:00',
        '2026-01-05 09:00','2026-01-06 11:00','DT_FixedDUR2','2026-01-01 10:00','2026-01-01 11:00',
        'CS_MSOA','2026-01-01 08:00','CS_MFOB','2026-01-09 17:00','37.5']
    lines=[];table=None
    for line in rich_xer().decode().splitlines():
        if line.startswith('%T\t'):table=line.split('\t')[1]
        if table=='TASK' and line.startswith('%F\t'):line+='\t'+'\t'.join(extra)
        elif table=='TASK' and line.startswith('%R\t'):line+='\t'+'\t'.join(values if line.split('\t')[1]=='0' else ['']*len(extra))
        lines.append(line)
        if table=='PROJWBS' and line.startswith('%R\tW1\t'):lines.append('%R\tW2\tP1\tCHILD\tChild WBS\tW1')
    return ('\n'.join(lines)+'\n').encode()
