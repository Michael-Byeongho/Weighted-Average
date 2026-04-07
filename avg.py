import streamlit as st
import pandas as pd

# 페이지 설정을 wide로 하면 더 넓게 쓸 수 있습니다.
st.set_page_config(layout="wide", page_title="가중평균 시뮬레이터")

st.title("⚖️ 가중평균 목표값 계산기")

# 메인 화면을 두 개의 큰 열로 분할
main_col1, main_col2 = st.columns([1, 1.2], gap="large")

# --- 왼쪽: 입력 섹션 ---
with main_col1:
    st.subheader("📋 화물 상세내용 입력")
    unit = st.selectbox("사용 단위 선택", ["%", "g/mt", "ppm"])
    is_upper_limit = st.checkbox(
    "패널티를 계산하나요? ", 
    value=False, 
    help="체크하면 비소 등 페널티를 계산(낮을수록 좋은) 하며, \n 체크하지 않을 시 높을수록 좋은 결과가 나오도록 계산합니다(구리/금/은 등)"
)    
    
    st.write("**[현재 상태]**")
    c1, c2 = st.columns(2)
    with c1:
        c_mass = st.number_input("📍 현재 중량 (톤)", value=100.0, step=1.0)
    with c2:
        c_val = st.number_input(f"📍 현재 성분 함량 ({unit})", value=2.5, step=0.01)

    st.write("**[추가 계획 및 목표]**")
    c3, c4 = st.columns(2)
    with c3:
        a_mass = st.number_input("➕ 추가 중량 (톤)", value=30.0, step=1.0)
    with c4:
        a_val_input = st.number_input(f"➕ 추가 성분 함량 ({unit})", value=0.10, step=0.01)
    
    t_val = st.number_input(f"🎯 목표 함량 ({unit})", value=0.4, step=0.01)

# --- 계산 로직 ---
total_mass = c_mass + a_mass
actual_mixed_val = (c_mass * c_val + a_mass * a_val_input) / total_mass
required_a_val = (t_val * total_mass - (c_mass * c_val)) / a_mass

# --- 오른쪽: 결과 섹션 ---
with main_col2:
    st.subheader("📊 계산 및 분석 결과")
    
    # [오류 방지] 계산에 필요한 변수들 다시 한번 체크 (계산 로직에서 정의되어 있어야 함)
    diff = actual_mixed_val - t_val
    min_possible = (c_mass * c_val) / total_mass
    
    # 1. 색상 및 방향성 로직 결정
    # 낮을수록 좋은 성분(상한제) : 목표보다 크면 빨간색(inverse)
    # 높을수록 좋은 성분(하한제) : 목표보다 크면 초록색(normal)
    d_color = "inverse" if is_upper_limit else "normal"

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric("페이퍼 블렌딩 중량", f"{total_mass:.1f} 톤")
    with res_col2:
        st.metric(
            f"페이퍼 블렌딩 결과 ({unit})", 
            f"{actual_mixed_val:.3f}", 
            delta=f"{diff:.3f} (목표대비)", 
            delta_color=d_color
        )

    st.divider()

    # 2. 목표 달성 여부 및 상세 가이드
    # 목표 달성 판정 로직
    is_success = actual_mixed_val <= t_val if is_upper_limit else actual_mixed_val >= t_val

    if is_success:
        st.success(f"### ✅ 목표 달성!")
        st.write(f"현재 블렌딩 결과가 목표 범위({t_val}{unit} {'이하' if is_upper_limit else '이상'}) 내에 있습니다.")


    else:
        st.error("### ❌ 목표 미달성")
        st.divider()
        st.subheader("🛠️ 해결 방법 시뮬레이션")
        st.info("현재 상황에서 조정 가능한 항목을 선택해 보세요.")

# 1. 사용자 상황 선택
    col_fix1, col_fix2 = st.columns(2)
    with col_fix1:
        adjust_mass = st.checkbox("중량(Qty) 조절 가능", value=True)
    with col_fix2:
        adjust_val = st.checkbox("품질(Quality) 조절 가능", value=False)

# 계산용 변수 준비
    denom = (t_val - a_val_input)  # 수식 일관성을 위해 방향 수정
    direction = "이하" if is_upper_limit else "이상"

# 2. 시나리오별 가이드 로직
    if adjust_mass and not adjust_val:
    # [시나리오 A: 물량만 조절]
    
    # [체크] 투입물(A)이 기존물(C)보다 목표에서 더 멀리 있는 경우 (희석 불가능 상황)
        is_impossible = (is_upper_limit and a_val_input > c_val and a_val_input > t_val and c_val > t_val) or \
                        (not is_upper_limit and a_val_input < c_val and a_val_input < t_val and c_val < t_val)

        if is_impossible:
            st.warning(f"⚠️ 현재 함량({a_val_input}{unit})은 목표보다 나빠서 양을 아무리 늘려도 해결되지 않습니다.")
            st.info("💡 '품질 조절 가능'을 함께 체크하여 요구되는 함량을 확인하세요.")
        elif a_val_input == t_val:
            st.info(f"💡 투입 화물이 목표치({t_val}{unit})와 같아 혼합비율로 품질을 바꿀 수 없습니다.")
        else:
        # 공식 계산
            needed_total_a_mass = c_mass * (t_val - c_val) / (a_val_input - t_val)
        
            if needed_total_a_mass < 0:
                st.info(f"✅ **이미 목표 달성 중:** 현재 화물을 추가해도 목표({t_val}{unit} {direction})를 벗어나지 않습니다.")
                st.write(f"(물량 조절 없이 현재 상태를 유지하셔도 무방합니다.)")            
            else:
                diff = needed_total_a_mass - a_mass
                if is_upper_limit and a_val_input > t_val:
                # 패널티 상황에서 나쁜 품질을 넣을 때
                    st.success(f"💡 **중량 제한 가이드:** 목표({t_val}{unit})를 넘지 않으려면 추가 화물을 **최대 {needed_total_a_mass:.1f}톤**까지만 투입해야 합니다.")
                else:
                # 일반적인 상황
                    st.success(f"💡 **중량 조절 가이드:** 추가 화물을 총 **{needed_total_a_mass:.1f}톤** 투입 시 목표 달성!")
            
            # 증감 수치 표시
                if diff > 0:
                    st.write(f"(현재보다 **{diff:.1f}톤** 추가 가능)")
                elif diff < 0:
                    st.write(f"(현재보다 **{abs(diff):.1f}톤** 줄여야 함)")

    elif adjust_val and not adjust_mass:
    # [시나리오 B: 품질만 조절]
        required_val = (t_val * (c_mass + a_mass) - (c_mass * c_val)) / a_mass
        st.success(f"💡 **품질 조절 가이드:** **{a_mass}톤**을 유지하려면 함량을 **{required_val:.3f}{unit} {direction}**으로 맞춰야 합니다.")
        if (is_upper_limit and required_val < 0):
             st.warning("⚠️ 요구되는 품질이 0보다 낮습니다. 중량을 줄이지 않으면 목표 달성이 불가능할 수 있습니다.")

    elif adjust_mass and adjust_val:
    # [시나리오 C: 둘 다 조절]
        st.success("💡 **유연한 조절 가이드:** 아래의 'Range 시뮬레이션' 표를 확인하세요.")

    else:
    # [시나리오 D: 선택 없음]
        st.warning("⚠️ 조절 가능한 항목을 선택해 주세요.")


# 3. 상세 Range 시뮬레이션 테이블
    with st.expander("📊 중량 변화에 따른 요구 함량 시뮬레이션", expanded=True):
        st.write("추가 투입할 중량의 범위를 설정하여 필요 함량을 확인하세요.")
    
    # 슬라이더로 중량 범위 설정 (현재 설정값의 0.1배 ~ 3배 범위)
        mass_range = st.slider(
        "시뮬레이션 중량 범위 (톤)",
            min_value=float(a_mass * 0.1),
            max_value=float(a_mass * 3.0),
            value=(float(a_mass * 0.5), float(a_mass * 1.5)), # 기본 선택 범위
            step=1.0
        )

    # 슬라이더 범위 내에서 10개 구간으로 나누어 계산
        import numpy as np
        test_masses = np.linspace(mass_range[0], mass_range[1], 10)
    
        data = []
        for m in test_masses:
            if m <= 0: continue
        # 역산 공식: p2 = [target * (m1 + m) - (m1 * p1)] / m
            req_v = (t_val * (c_mass + m) - (c_mass * c_val)) / m
        
        # 성격에 따른 상태 및 텍스트 결정
            if is_upper_limit:
                status = "🟢 가능" if req_v >= 0 else "🔴 불가"
                val_text = f"{req_v:.3f} 이하" if req_v >= 0 else "도달 불가"
            else:
            # 하한선일 경우, 계산된 값보다 높아야 함
                status = "🟢 가능" if req_v <= 100 else "🔴 불가" # 100% 초과 방지 등
                val_text = f"{req_v:.3f} 이상"
        
            data.append({
            "추가 중량(톤)": f"{m:.1f}",
            f"요구 함량({unit})": val_text,
            "상태": status
        })
    
    # 테이블 출력
        st.table(pd.DataFrame(data))