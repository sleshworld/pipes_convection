import tkinter as tk
from tkinter import ttk, scrolledtext, BooleanVar, Checkbutton
from math import log, pi
from Nu import Nu
from Material import Material
from buttons import show_error_popup, show_about
from radiantion import radiation


def a(nusselt: float, lambd: float, d: float):
    return nusselt * lambd / d


def calculate():
    path_external = entry_path_external.get()
    path_internal = entry_path_internal.get()
    is_use_radiation = rad.get()

    if path_external == 'water':
        is_gaz_external = False
    else:
        is_gaz_external = True
    if path_internal == 'water':
        is_gaz_internal = False
    else:
        is_gaz_internal = True

    t_inlet = float(entry_t_inlet.get())
    t_out = float(entry_t_out.get())
    t_external = float(entry_t_external.get())

    if is_gaz_internal and (t_inlet < -50 or t_inlet > 1200):
        show_error_popup('Неверная входная температура (-50 C < T < 1200 C)')
    if is_gaz_external and (t_external < -50 or t_inlet > 1200):
        show_error_popup('Неверная внешняя температура (-50 C < T < 1200 C)')
    if not is_gaz_internal and (t_inlet < 0 or t_inlet > 100):
        show_error_popup('Неверная входная температура (0 C < T < 100 C)')
    if is_gaz_external and (t_external < 0 or t_inlet > 100):
        show_error_popup('Неверная внешняя температура (0 C < T < 100 C)')

    if (t_out > t_inlet and t_external < t_inlet) or (t_out < t_inlet and t_external > t_inlet):
        show_error_popup('Неверная выходная температура')

    d_in = float(entry_d_in.get())
    d_external = float(entry_d_external.get())
    if d_in >= d_external or d_in == 0:
        show_error_popup('Неверные параметры трубы')

    v_external = float(entry_v_external.get())
    v_in = float(entry_v_in.get())
    if v_in <= 1e-6 or v_external <= 1e-6 or v_in > 3e+8 or v_external > 3e+8:
        show_error_popup('Неверное значение скорости')

    p_inlet = float(entry_p_inlet.get())
    p_external = float(entry_p_external.get())
    if p_inlet <= 0 or p_external <= 0:
        show_error_popup('Неверное значение давления')

    lambda_pipe = float(entry_lambda_pipe.get())
    if lambda_pipe <= 0 or lambda_pipe >= 1e+5:
        show_error_popup('Неверное значение теплопроводности трубы')

    t_avg = (t_inlet + t_out) / 2
    t_wall = (t_external + t_avg) / 2
    delta_T_max = max((t_inlet - t_external), (t_out - t_external))
    delta_T_min = min((t_inlet - t_external), (t_out - t_external))
    delta_T_ln = (delta_T_max - delta_T_min) / log(delta_T_max / delta_T_min)

    # свойства материалов при заданной температуре и давлении
    material_external = Material(T=t_external, p=p_external, path=path_external)
    material_in_wall = Material(T=t_wall, p=p_inlet, path=path_internal)
    material_in_avg = Material(T=t_avg, p=p_inlet, path=path_internal)
    material_in_inlet = Material(T=t_inlet, p=p_inlet, path=path_internal)

    Re_in = material_in_avg.ro * v_in * d_in / material_in_avg.Mu
    Re_external = material_external.ro * v_external * d_external / material_external.Mu  # Re для внешнего течения

    avg_Nu_external = Nu.NuExternal(Re=Re_external, Pr=material_external.Pr,
                                    is_gaz=is_gaz_external).calculate()  # Уонг стр 72
    a_external = a(nusselt=avg_Nu_external, lambd=material_external.lambd, d=d_external)  # коэф теплоотдачи внешний

    if is_use_radiation and is_gaz_external:
        a_external += radiation(t_wall)

    avg_Nu_in = Nu.NuInternal(Re=Re_in, Pr=material_in_avg.Pr, is_gaz=is_gaz_internal,
                              Mu=material_in_avg.Mu, Mu_wall=material_in_wall.Mu).calculate()  # Уонг стр 68
    a_in = a(nusselt=avg_Nu_in, lambd=material_in_avg.lambd, d=d_in)  # коэф теплоотдачи внутренний

    k_l = pi * (1 / (a_in * d_in) + log(d_external / d_in) / (2 * lambda_pipe) + 1 / (
            a_external * d_external)) ** -1  # линейный коэф теплоотдачи, Исаченко стр 37

    l = material_in_inlet.ro * v_in * material_in_inlet.c_p * pi * ((d_in / 2) ** 2) * (t_inlet - t_out) / (
            k_l * delta_T_ln)  # из уравнения теплового баланса
    delta_p = 0.184 / (Re_in ** 0.2) * (l / d_in) * (0.5 * material_in_inlet.ro * v_in ** 2)

    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, f'Re external: {Re_external[0]:.5}\nRe internal: {Re_in[0]:.5}\n')
    output_text.insert(tk.END, f'ΔT max: {delta_T_max:.5} °C\nΔT min: {delta_T_min:.5} °C\n')
    output_text.insert(tk.END, f'ΔT log: {delta_T_ln:.5}\navarage T: {t_avg:.6} °C\nwall T: {t_wall:.5} °C\n')
    output_text.insert(tk.END,
                       f'Nu external: {avg_Nu_external[0]:.5}\nα external: {a_external[0]:.5} Вт/(м^2·K)\n')
    output_text.insert(tk.END, f'Nu internal: {avg_Nu_in[0]:.5}\nα internal: {a_in[0]:.5} Вт/(м^2·K)\n')
    output_text.insert(tk.END,
                       f'Линейный коэффциент теплопередачи: {k_l[0]:.5} Вт/(м·K)\n')
    output_text.insert(tk.END, f'Длина трубы: {l[0]:.5} м\nПерепад давления: {delta_p[0]:.5} Па')


root = tk.Tk()
root.title("Конвекция 1.1.1")

label_t_inlet = tk.Label(root, text="Входная температура, °C")
label_t_inlet.grid(row=0, column=0)
entry_t_inlet = tk.Entry(root)
entry_t_inlet.grid(row=0, column=1)
entry_t_inlet.insert(0, "80")

label_t_out = tk.Label(root, text="Выходная температура, °C")
label_t_out.grid(row=1, column=0)
entry_t_out = tk.Entry(root)
entry_t_out.grid(row=1, column=1)
entry_t_out.insert(0, "50.5")

label_t_external = tk.Label(root, text="Температура внешней среды, °C")
label_t_external.grid(row=2, column=0)
entry_t_external = tk.Entry(root)
entry_t_external.grid(row=2, column=1)
entry_t_external.insert(0, "0")

label_p_inlet = tk.Label(root, text="Внутреннее входное давление, атм")
label_p_inlet.grid(row=3, column=0)
entry_p_inlet = tk.Entry(root)
entry_p_inlet.grid(row=3, column=1)
entry_p_inlet.insert(0, "1")

label_p_external = tk.Label(root, text="Внешнее давление, атм")
label_p_external.grid(row=4, column=0)
entry_p_external = tk.Entry(root)
entry_p_external.grid(row=4, column=1)
entry_p_external.insert(0, "1")

label_d_in = tk.Label(root, text="Внутренний диаметр трубы, м")
label_d_in.grid(row=5, column=0)
entry_d_in = tk.Entry(root)
entry_d_in.grid(row=5, column=1)
entry_d_in.insert(0, "0.014")

label_d_external = tk.Label(root, text="Внешний диаметр трубы, м")
label_d_external.grid(row=6, column=0)
entry_d_external = tk.Entry(root)
entry_d_external.grid(row=6, column=1)
entry_d_external.insert(0, "0.02")

label_v_external = tk.Label(root, text="Скорость внешнего течения, м/с")
label_v_external.grid(row=7, column=0)
entry_v_external = tk.Entry(root)
entry_v_external.grid(row=7, column=1)
entry_v_external.insert(0, "2")

label_v_in = tk.Label(root, text="Скорость внутреннего течения, м/с")
label_v_in.grid(row=8, column=0)
entry_v_in = tk.Entry(root)
entry_v_in.grid(row=8, column=1)
entry_v_in.insert(0, "0.089")

label_lambda_pipe = tk.Label(root, text="Теплопроводность трубы, Вт/(м·K)")
label_lambda_pipe.grid(row=9, column=0)
entry_lambda_pipe = tk.Entry(root)
entry_lambda_pipe.grid(row=9, column=1)
entry_lambda_pipe.insert(0, "0.24")

label_path_external = tk.Label(root, text="Наружная жидкость")
label_path_external.grid(row=10, column=0)
entry_path_external = ttk.Combobox(root, values=["water", "air"])
entry_path_external.grid(row=10, column=1)
entry_path_external.current(1)

label_path_internal = tk.Label(root, text="Внутренняя жидкость")
label_path_internal.grid(row=11, column=0)
entry_path_internal = ttk.Combobox(root, values=["water", "air"])
entry_path_internal.grid(row=11, column=1)
entry_path_internal.current(0)

label_rad = tk.Label(root, text="Учитывать излучение")
label_rad.grid(row=12, column=0)
rad = BooleanVar()
entry_rad = Checkbutton(root, variable=rad)
entry_rad.grid(row=12, column=1)

button_calculate = tk.Button(root, text="Calculate", command=calculate)
button_calculate.grid(row=13, columnspan=2)

output_text = scrolledtext.ScrolledText(root, width=50, height=14, wrap=tk.WORD)
output_text.grid(row=14, columnspan=2)

button_clear = tk.Button(root, text="About", command=show_about)
button_clear.grid(row=15, columnspan=2)

root.mainloop()
