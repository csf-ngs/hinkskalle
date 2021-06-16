<template>
  <v-container>
      <v-row v-for="tag in manifest.tags" :key="tag">
        <v-col>
          <hsk-text-input :label="'Pull '+tag" :static-value="manifest.pullCmd(tag)"></hsk-text-input>
        </v-col>
      </v-row>
        <v-row justify="center" v-if="localState.imgConfig">
          <v-col cols="12">
            <hsk-text-input label="Created" :static-value="localState.imgConfig.created | moment('YYYY-MM-DD HH:mm:ss')"></hsk-text-input>
            <hsk-text-input label="Docker Version" :static-value="localState.imgConfig.dockerVersion"></hsk-text-input>
            <hsk-text-input label="OS" :static-value="localState.imgConfig.os"></hsk-text-input>
            <hsk-text-input label="VCS Link" :static-value="vcsLink"></hsk-text-input>
            <hsk-text-input v-for="(value, label) in localState.imgConfig.labels" :key="label"
              :static-value="value" :label="label"></hsk-text-input>
          </v-col>
        </v-row>
        <v-row justify="center" v-if="localState.history">
          <v-col cols="11">
            <h3 class="mb-3">History</h3>
            <v-timeline dense>
              <v-timeline-item v-for="(hist,i) of localState.history" :key="i" :color="hist.color">
                <v-card class="elevation-1">
                  <v-card-title>
                    {{hist.created | moment('YYYY-MM-DD HH:mm:ss')}} -
                    <span v-if="hist.emptyLayer" class="ml-1">
                      (empty)
                    </span>
                    <span v-else class="ml-1">
                      {{hist.layer.size | prettyBytes()}}
                    </span>
                  </v-card-title>
                  <v-card-text><code>{{hist.command}}</code></v-card-text>
                </v-card>
              </v-timeline-item>
            </v-timeline>
          </v-col>
        </v-row>
  </v-container>
</template>
<script lang="ts">
import { Manifest } from '@/store/models';
import Vue from 'vue';

import { map as _map, max as _max, round as _round, filter as _filter, sortBy as _sortBy, each as _each } from 'lodash';

interface ImageConfig {
  created: Date;
  dockerVersion: string;
  os: string;
  labels: any;
}

interface Layer {
  digest: string;
  size: number;
}
interface History {
  created: Date;
  command: string;
  emptyLayer: boolean;
  layer?: Layer;
  color?: string;
}

interface State {
  imgConfig: ImageConfig | null;
  history: History[];
  layers: Layer[];
}

export default Vue.extend({
  name: 'DockerDetails',
  props: {
    manifest: {
      type: Manifest,
      required: true,
    },
  },
  mounted: function() {
    this.loadConfig();
    this.localState.layers = _map(this.manifest.content.layers, l => ({
      size: l.size, digest: l.digest
    }));
  },
  data: (): { localState: State } => ({
    localState: {
      imgConfig: null,
      history: [],
      layers: [],
    },
  }),
  computed: {
    vcsLink: function(): string {
      if (!this.localState.imgConfig || !this.localState.imgConfig.labels) {
        return '';
      }
      return this.localState.imgConfig.labels['org.label-schema.vcs-url'];
    }
  },
  methods: {
    loadConfig() {
      this.$store.dispatch('manifests/getConfig', this.manifest)
        .then(config => {
          this.localState.imgConfig = {
            created: new Date(config.created),
            dockerVersion: config.docker_version,
            os: config.os,
            labels: config.config.Labels,
          };
          this.localState.history = _map(config.history, item => {
            const entry = { 
              created: new Date(item.created), 
              command: item.created_by, 
              emptyLayer: item.empty_layer,
              color: 'blue-grey lighten-5',
            };
            return entry;
          });
          const maxSize = _max(_map(this.localState.layers, 'size')) || 1;
          const historyWithLayer = _filter(this.localState.history, h => !h.emptyLayer);
          _each(historyWithLayer, (h, idx) => {
            h.layer = this.localState.layers[idx];
            const relSize = _round(h.layer.size/maxSize*10)-5;
            h.color = `blue-grey ${relSize < 0 ? 'lighten' : relSize > 0 ? 'darken' : ''}-${Math.abs(relSize)}`
          });
          this.localState.history = _sortBy(this.localState.history, 'created');
          console.log(this.localState.history);
        })
        .catch(err => this.$store.commit('snackbar/showError', err))
    }
  },
})

</script>