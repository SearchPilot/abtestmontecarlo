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
    if rand < 0.5:
        return 'A'
    else:
        return 'B'

def did_it_convert(channel, variant, channel_conv):
    rand = random.random()
    prob = channel_conv[channel][variant]
    return rand < prob

def single_trial(num_views, channel_mix, channel_conv):
    count = {'A': 0, 'B': 0}
    result_array = {"A": [{'conv': 0, 'views': 0}, {'conv': 0, 'views': 0}], "B": [{'conv': 0, 'views': 0}, {'conv': 0, 'views': 0}]}
    for i in range(0,num_views-1):
        channel = which_channel(channel_mix)
        variant = which_variant()
        result_array[variant][channel]['views'] += 1
        if did_it_convert(channel, variant, channel_conv):
            result_array[variant][channel]['conv'] += 1
    aggregate_array = {"A": {'conv': result_array['A'][0]['conv'] + result_array['A'][1]['conv'], 'views': result_array['A'][0]['views'] + result_array['A'][1]['views']}, "B": {'conv': result_array['B'][0]['conv'] + result_array['B'][1]['conv'], 'views': result_array['B'][0]['views'] + result_array['B'][1]['views']}}
    return result_array, aggregate_array

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
    p_total = pvalue(z_score(trial[1]))
    channel1_trial = {'A': trial[0]['A'][0], 'B': trial[0]['B'][0]}
    channel2_trial = {'A': trial[0]['A'][1], 'B': trial[0]['B'][1]}
    p_1 = pvalue(z_score(channel1_trial))
    p_2 = pvalue(z_score(channel2_trial))
    return trial[0], trial[1], p_total, p_1, p_2

def single_monte_carlo(mix, conversion_rates, run_length_multiple):
    blended_conv = mix[0]*conversion_rates[0]['A'] + mix[1]*conversion_rates[1]['A']
    delta = 0.01 # minimum effect we want to detect
    num_views = int(16 * blended_conv * (1-blended_conv) / (delta*delta)) # based off sample sizes from http://www.evanmiller.org/how-not-to-run-an-ab-test.html
    num_views *= run_length_multiple
    total_count = 0
    individual_count = 0
    test_p = 0.95
    for i in range(0,500):
        individual, overall, p_total, p_1, p_2 = analyse_trial(num_views, mix, conversion_rates)
        if p_total >= test_p:
            total_count += 1
            if p_1 < test_p and p_2 < test_p:
                individual_count += 1

    print ""+str(mix[0])+","+str(mix[1])+","+str(conversion_rates[0]['A'])+","+str(conversion_rates[0]['B'])+","+str(conversion_rates[1]['A'])+","+str(conversion_rates[1]['B'])+","+str(run_length_multiple)+","+str(total_count)+","+str(individual_count)+","+str(test_p - float(individual_count) / float(total_count))

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
