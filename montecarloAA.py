import random
import math

def which_channel(channel_mix):
    rand = random.random()
    if rand < channel_mix[0]:
        return 0
    else:
        return 1

def which_variant():
    rand = random.random()
    if rand < 0.25:
        return 'A1'
    elif rand < 0.5:
        return 'A2'
    elif rand < 0.75:
        return 'B1'
    else:
        return 'B2'

def did_it_convert(channel, variant, channel_conv):
    rand = random.random()
    prob = channel_conv[channel][variant]
    return rand < prob

def single_trial(num_views, channel_mix, channel_conv):
    result_array = {"A1": {'conv': 0, 'views': 0}, "A2": {'conv': 0, 'views': 0}, "B1": {'conv': 0, 'views': 0}, "B2": {'conv': 0, 'views': 0}}
    for i in range(0,num_views-1):
        channel = which_channel(channel_mix)
        variant = which_variant()
        result_array[variant]['views'] += 1
        if did_it_convert(channel, variant[0], channel_conv):
            result_array[variant]['conv'] += 1
    return result_array

# from the source of https://mixpanel.com/labs/split-test-calculator
def z_score(values):
    try:
        prob = float(values['A']['conv'] + values['B']['conv']) / float(values['A']['views'] + values['B']['views'])
        sp = math.sqrt(prob * (1-prob) * (1/float(values['A']['views']) + 1/float(values['B']['views'])))
        score = (float(values['A']['conv']) / float(values['A']['views']) - float(values['B']['conv']) / float(values['B']['views'])) / float(sp)
        return score
    except:
        #print "zero division"
        return 0

def pvalue(zscore):
    Z_TABLE = [[0.70, 0.53], [0.80, 0.85], [0.90, 1.29], [0.95, 1.65], [0.99, 2.33], [0.999, 3.08]]
    found_p = 0
    if zscore == 0:
        return 0
    for z in range(0,len(Z_TABLE)):
        if math.fabs(zscore) >= Z_TABLE[z][1]:
            found_p = Z_TABLE[z][0]
    return found_p

def analyse_trial(num_views, channel_mix, channel_conv):
    trial = single_trial(num_views, channel_mix, channel_conv)
    p_a = pvalue(z_score({"A": trial['A1'], "B": trial['A2']}))
    p_b = pvalue(z_score({"A": trial['B1'], "B": trial['B2']}))
    p_a_b = pvalue(z_score({"A": trial['A1'], "B": trial['B1']}))
    return trial, p_a, p_b, p_a_b

def single_monte_carlo(mix, conversion_rates, run_length_multiple):
    blended_conv = mix[0]*conversion_rates[0]['A'] + mix[1]*conversion_rates[1]['A']
    delta = 0.01 # minimum effect we want to detect
    num_views = int(16 * blended_conv * (1-blended_conv) / (delta*delta)) # based off sample sizes from http://www.evanmiller.org/how-not-to-run-an-ab-test.html
    num_views *= 2 # since we are running A/A/B/B we have to run for twice as long as A/B
    num_views *= run_length_multiple
    significant_count = 0
    no_significance_count = 0
    duff_test = 0
    test_p = 0.95
    for i in range(0,500):
        trial, p_a, p_b, p_a_b= analyse_trial(num_views, mix, conversion_rates)
        if p_a < test_p and p_b < test_p:
            if p_a_b >= test_p:
                significant_count += 1
            else:
                no_significance_count += 1
        else:
            duff_test += 1

    print ""+str(mix[0])+","+str(mix[1])+","+str(conversion_rates[0]['A'])+","+str(conversion_rates[0]['B'])+","+str(conversion_rates[1]['A'])+","+str(conversion_rates[1]['B'])+","+str(run_length_multiple)+","+str(significant_count)+","+str(no_significance_count)+","+str(duff_test)

# first, iterate over the channel blend
for blend in [0.03]:
    # then, iterate over the conversion rates
    for conv_A in [0.002 * n for n in range(5,10)]:
        for channel_0_multiplier in [1+0.2 * n for n in range(1,4)]:
            for B_uplift in [1+0.2*n for n in range(1,4)]:
                conv_rates = [{"A": conv_A*channel_0_multiplier, "B": conv_A*channel_0_multiplier*B_uplift}, {"A": conv_A, "B": conv_A*B_uplift}]
                # finally, iterate over the run length multiple
                for multiple in [1,2,4,8]:
                    single_monte_carlo([blend, 1-blend], conv_rates, multiple)
