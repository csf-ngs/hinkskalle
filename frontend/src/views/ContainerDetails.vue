<template>
  <div class="container-details">
    <top-bar :title="title">
      <template v-if="localState.container">
        <v-badge :content="localState.container.stars" overlap>
          <v-icon large>mdi-star</v-icon>
        </v-badge>
        <v-badge :content="localState.container.downloadCount" overlap>
          <v-icon large>mdi-download</v-icon>
        </v-badge>
      </template>
    </top-bar>
    <v-container v-if="localState.container">
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-row>
            <v-col>
              <v-text-field :value="localState.container.name" label="Name" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
            </v-col>
          </v-row>
          <v-row dense>
            <v-col>
              <v-text-field :value="localState.container.createdAt | moment('YYYY-MM-DD HH:mm:ss')" label="Created" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
            </v-col>
            <v-col>
              <v-text-field :value="localState.container.createdBy" label="Created By" outlined readonly append-icon="mdi-lock-outline"></v-text-field>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-text-field v-model="localState.container.vcsUrl" label="Git/CVS URL" outlined></v-text-field>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-text-field v-model="localState.container.description" label="Description" outlined></v-text-field>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-textarea v-model="localState.container.fullDescription" label="Full Description" outlined></v-textarea>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <v-select v-model="localState.container.private" label="Private" outlined :items="[ { value: false, text: 'no' }, { value: true, text: 'yes' } ]"></v-select>
            </v-col>
            <v-col>
              <v-select v-model="localState.container.readOnly" label="Readonly" outlined :items="[ { value: false, text: 'no' }, { value: true, text: 'yes' } ]"></v-select>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { Container, Image } from '../store/models';

interface State {
  container: Container | null;
  images: Image[];
}

export default Vue.extend({
  name: 'ContainerDetails',
  mounted() {
    this.loadContainer();
  },
  data: (): { localState: State } => ({
    localState: {
      container: null,
      images: [],
    }
  }),
  computed: {
    title(): string {
      return `Container Details for ${this.localState.container ? this.localState.container.fullPath : '...'}`
    },
    loading(): boolean {
      return this.$store.getters['container/status']==='loading';
    },
  },
  methods: {
    loadContainer() {
      this.$store.dispatch('containers/get', { entity: this.$route.params.entity, collection: this.$route.params.collection, container: this.$route.params.container })
        .then((container: Container) => {
          this.localState.container = container;
          return this.$store.dispatch('images/list', container);
        })
        .then((images: Image[]) => {
          this.localState.images = images;
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    }
  }
});
</script>